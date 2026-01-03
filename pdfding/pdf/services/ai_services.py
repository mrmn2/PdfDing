"""
AI Services for PdfDing
This module provides AI-powered summarization and Q&A capabilities for PDF annotations.
"""

import os
from typing import List, Dict, Optional, Tuple
from django.conf import settings
from pdf.models.pdf_models import Pdf, PdfHighlight, PdfComment
from openai import OpenAI
from decouple import config
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        """Initialize the AI service with OpenAI client."""
        # Debug logging
        logger.info("Initializing AIService...")
        
        # Try to get API key from different sources
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            api_key = config('OPENAI_API_KEY', default='')
        
        logger.info(f"API key from settings: {'SET' if getattr(settings, 'OPENAI_API_KEY', None) else 'NOT SET'}")
        logger.info(f"API key from env: {'SET' if config('OPENAI_API_KEY', default=None) else 'NOT SET'}")
        logger.info(f"API key length: {len(api_key) if api_key else 0}")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in settings or environment variables")
        
        base_url = getattr(settings, 'OPENAI_BASE_URL', None)
        if not base_url:
            base_url = config('OPENAI_BASE_URL', default='https://api.openai.com/v1')
        
        self.model = getattr(settings, 'OPENAI_MODEL', None)
        if not self.model:
            self.model = config('OPENAI_MODEL', default='gpt-3.5-turbo')
        
        logger.info(f"Base URL: {base_url}")
        logger.info(f"Model: {self.model}")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
    
    def _get_annotations_for_pdf(self, pdf: Pdf) -> List[Dict]:
        """
        Retrieve all annotations (highlights and comments) for a PDF.
        
        Args:
            pdf: Pdf object
            
        Returns:
            List of annotation dictionaries with text, page, and type
        """
        annotations = []
        
        # Get highlights
        highlights = PdfHighlight.objects.filter(pdf=pdf).order_by('page')
        for highlight in highlights:
            annotations.append({
                'text': highlight.text,
                'page': highlight.page,
                'type': 'highlight',
                'creation_date': highlight.creation_date,
                'pdf_name': pdf.name
            })
        
        # Get comments
        comments = PdfComment.objects.filter(pdf=pdf).order_by('page')
        for comment in comments:
            annotations.append({
                'text': comment.text,
                'page': comment.page,
                'type': 'comment',
                'creation_date': comment.creation_date,
                'pdf_name': pdf.name
            })
        
        # Sort by page and then by creation date
        annotations.sort(key=lambda x: (x['page'], x['creation_date']))
        return annotations
    
    def _get_annotations_for_list(self, annotation_objects: List) -> List[Dict]:
        """
        Retrieve all annotations from a list of annotation objects.
        
        Args:
            annotation_objects: List of annotation objects (PdfHighlight or PdfComment)
            
        Returns:
            List of annotation dictionaries with text, page, and type
        """
        annotations = []
        
        for annotation in annotation_objects:
            if isinstance(annotation, PdfHighlight):
                annotations.append({
                    'text': annotation.text,
                    'page': annotation.page,
                    'type': 'highlight',
                    'creation_date': annotation.creation_date,
                    'pdf_name': annotation.pdf.name
                })
            elif isinstance(annotation, PdfComment):
                annotations.append({
                    'text': annotation.text,
                    'page': annotation.page,
                    'type': 'comment',
                    'creation_date': annotation.creation_date,
                    'pdf_name': annotation.pdf.name
                })
        
        # Sort by page and then by creation date
        annotations.sort(key=lambda x: (x['page'], x['creation_date']))
        return annotations
    
    def _format_annotations_for_prompt(self, annotations: List[Dict]) -> str:
        """
        Format annotations for use in AI prompts.
        
        Args:
            annotations: List of annotation dictionaries
            
        Returns:
            Formatted string of annotations
        """
        if not annotations:
            return "No annotations found."
        
        formatted = []
        for annotation in annotations:
            if 'pdf_name' in annotation:
                formatted.append(
                    f"[{annotation['pdf_name']}, Page {annotation['page']}] {annotation['type'].title()}: {annotation['text']}"
                )
            else:
                formatted.append(
                    f"[Page {annotation['page']}] {annotation['type'].title()}: {annotation['text']}"
                )
        
        return "\n".join(formatted)
    
    def summarize_annotations(self, pdf: Pdf, max_length: str = "medium") -> str:
        """
        Generate a summary of all annotations for a PDF.
        
        Args:
            pdf: Pdf object
            max_length: Summary length - "short", "medium", or "long"
            
        Returns:
            Summary text
        """
        annotations = self._get_annotations_for_pdf(pdf)
        
        if not annotations:
            return "No annotations found for this PDF."
        
        return self._summarize_annotations_internal(annotations, max_length)
    
    def summarize_annotations_for_list(self, annotation_objects: List, max_length: str = "medium") -> str:
        """
        Generate a summary of all annotations from a list.
        
        Args:
            annotation_objects: List of annotation objects
            max_length: Summary length - "short", "medium", or "long"
            
        Returns:
            Summary text
        """
        annotations = self._get_annotations_for_list(annotation_objects)
        
        if not annotations:
            return "No annotations found to summarize."
        
        return self._summarize_annotations_internal(annotations, max_length)
    
    def _summarize_annotations_internal(self, annotations: List[Dict], max_length: str = "medium") -> str:
        """
        Internal method to generate a summary of annotations.
        
        Args:
            annotations: List of annotation dictionaries
            max_length: Summary length - "short", "medium", or "long"
            
        Returns:
            Summary text
        """
        length_instructions = {
            "short": "Provide a brief summary (2-3 sentences) of the key points.",
            "medium": "Provide a comprehensive summary (5-7 sentences) covering the main themes.",
            "long": "Provide a detailed summary (8-10 sentences) with specific examples and insights."
        }
        
        formatted_annotations = self._format_annotations_for_prompt(annotations)
        
        prompt = f"""
        Please analyze the following annotations from PDF documents and create a summary.
        
        {length_instructions.get(max_length, length_instructions["medium"])}
        
        Annotations:
        {formatted_annotations}
        
        Summary:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that creates clear, organized summaries of PDF annotations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500 if max_length == "short" else 1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def answer_question_about_annotations(self, pdf: Pdf, question: str) -> str:
        """
        Answer a question about the annotations in a PDF.
        
        Args:
            pdf: Pdf object
            question: User's question about the annotations
            
        Returns:
            Answer text
        """
        annotations = self._get_annotations_for_pdf(pdf)
        
        if not annotations:
            return "No annotations found for this PDF."
        
        formatted_annotations = self._format_annotations_for_prompt(annotations)
        
        prompt = f"""
        I have the following annotations from a PDF document. Please answer the question 
        according to these annotations. If the answer cannot be found in the annotations, 
        please say so.
        
        Annotations:
        {formatted_annotations}
        
        Question: {question}
        
        Answer:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that answers questions based on PDF annotations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return f"Error answering question: {str(e)}"
    
    def ask_question_with_context(self, prompt: str) -> str:
        """
        Ask a question with provided context.
        
        Args:
            prompt: Formatted prompt with context and question
            
        Returns:
            Answer text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that answers questions based on provided text context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error asking question with context: {str(e)}")
            return f"Error processing request: {str(e)}"
    
    def extract_key_themes(self, pdf: Pdf) -> List[str]:
        """
        Extract key themes from annotations.
        
        Args:
            pdf: Pdf object
            
        Returns:
            List of key themes
        """
        annotations = self._get_annotations_for_pdf(pdf)
        
        if not annotations:
            return []
        
        return self._extract_key_themes_internal(annotations)
    
    def extract_key_themes_for_list(self, annotation_objects: List) -> List[str]:
        """
        Extract key themes from a list of annotations.
        
        Args:
            annotation_objects: List of annotation objects
            
        Returns:
            List of key themes
        """
        annotations = self._get_annotations_for_list(annotation_objects)
        
        if not annotations:
            return []
        
        return self._extract_key_themes_internal(annotations)
    
    def _extract_key_themes_internal(self, annotations: List[Dict]) -> List[str]:
        """
        Internal method to extract key themes from annotations.
        
        Args:
            annotations: List of annotation dictionaries
            
        Returns:
            List of key themes
        """
        formatted_annotations = self._format_annotations_for_prompt(annotations)
        
        prompt = f"""
        Please extract 5-10 key themes or topics from the following PDF annotations. 
        Return only the themes, one per line, without any additional text or numbering.
        
        Annotations:
        {formatted_annotations}
        
        Key themes:
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant that extracts key themes from text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            themes = response.choices[0].message.content.strip().split('\n')
            return [theme.strip() for theme in themes if theme.strip()]
        except Exception as e:
            logger.error(f"Error extracting themes: {str(e)}")
            return []

# Global instance
ai_service: Optional[AIService] = None

def get_ai_service() -> Optional[AIService]:
    """
    Get the AI service instance, creating it if it doesn't exist.
    
    Returns:
        AIService instance or None if API key is not configured
    """
    global ai_service
    
    if ai_service is None:
        try:
            ai_service = AIService()
            logger.info("AI service initialized successfully")
            # Log if API key is set (without exposing the actual key)
            import os
            api_key = os.environ.get('OPENAI_API_KEY', '')
            if api_key:
                logger.info(f"OpenAI API key is set (length: {len(api_key)} characters)")
            else:
                logger.warning("OpenAI API key is not set in environment variables")
        except ValueError as e:
            logger.warning(f"OpenAI API key not found. AI features will be disabled. Error: {e}")
            return None
        except Exception as e:
            logger.error(f"Error initializing AI service: {e}")
            return None
    
    return ai_service
