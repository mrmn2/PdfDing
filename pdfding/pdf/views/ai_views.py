"""
Views for AI-powered features in PdfDing
"""

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib import messages
from django.utils import timezone
from pdf.models.pdf_models import Pdf, PdfHighlight, PdfComment
from pdf.services.ai_services import get_ai_service


class AISummarizeView(View):
    """View for generating AI summaries of PDF annotations."""
    
    def get(self, request: HttpRequest, identifier: str):
        """Display the AI summary interface."""
        if identifier == 'all':
            # Handle overview summary for all PDFs
            pdfs = request.user.profile.current_pdfs.all()
            return render(request, 'partials/ai/ai_summary.html', {
                'pdfs': pdfs,
                'summary': None
            })
        else:
            pdf = get_object_or_404(Pdf, id=identifier)
            
            # Check if user has access to this PDF
            if pdf.workspace not in request.user.profile.workspaces.all():
                messages.error(request, "You don't have access to this PDF.")
                return render(request, 'partials/ai/ai_summary.html', {
                    'error': "You don't have access to this PDF."
                })
            
            return render(request, 'partials/ai/ai_summary.html', {
                'pdf': pdf,
                'summary': None
            })
    
    def post(self, request: HttpRequest, identifier: str):
        """Generate an AI summary of the PDF annotations."""
        if identifier == 'all':
            # Handle overview summary for all PDFs
            pdfs = request.user.profile.current_pdfs.all()
            
            # Get AI service
            ai_service = get_ai_service()
            if ai_service is None:
                if request.htmx:
                    return render(request, 'partials/ai/ai_inline_summary_result.html', {
                        'error': "AI service is not configured. Please contact the administrator."
                    })
                return JsonResponse({
                    'error': "AI service is not configured. Please contact the administrator."
                }, status=500)
            
            # For overview, we'll summarize all annotations
            all_annotations = []
            for pdf in pdfs:
                highlights = PdfHighlight.objects.filter(pdf=pdf)
                comments = PdfComment.objects.filter(pdf=pdf)
                all_annotations.extend(list(highlights) + list(comments))
            
            if not all_annotations:
                if request.htmx:
                    return render(request, 'partials/ai/ai_inline_summary_result.html', {
                        'error': "No annotations found to summarize."
                    })
                return JsonResponse({
                    'error': "No annotations found to summarize."
                })
            
            # Generate summary for all annotations
            summary_length = request.POST.get('length', 'medium')
            summary = ai_service.summarize_annotations_for_list(all_annotations, summary_length)
            
            if request.htmx:
                return render(request, 'partials/ai/ai_inline_summary_result.html', {
                    'summary': summary,
                    'length': summary_length
                })
            else:
                return JsonResponse({
                    'summary': summary
                })
        else:
            pdf = get_object_or_404(Pdf, id=identifier)
            
            # Check if user has access to this PDF
            if pdf.workspace not in request.user.profile.workspaces.all():
                if request.htmx:
                    return render(request, 'partials/ai/ai_inline_summary_result.html', {
                        'error': "You don't have access to this PDF."
                    })
                return JsonResponse({
                    'error': "You don't have access to this PDF."
                }, status=403)
            
            # Get AI service
            ai_service = get_ai_service()
            if ai_service is None:
                if request.htmx:
                    return render(request, 'partials/ai/ai_inline_summary_result.html', {
                        'error': "AI service is not configured. Please contact the administrator."
                    })
                return JsonResponse({
                    'error': "AI service is not configured. Please contact the administrator."
                }, status=500)
            
            # Get summary length from request
            summary_length = request.POST.get('length', 'medium')
            
            # Generate summary
            summary = ai_service.summarize_annotations(pdf, summary_length)
            
            if request.htmx:
                return render(request, 'partials/ai/ai_inline_summary_result.html', {
                    'pdf': pdf,
                    'summary': summary,
                    'length': summary_length
                })
            else:
                return JsonResponse({
                    'summary': summary
                })


class AIQuestionView(View):
    """View for answering questions about PDF annotations using AI."""
    
    def post(self, request: HttpRequest, identifier: str):
        """Answer a question about PDF annotations."""
        pdf = get_object_or_404(Pdf, id=identifier)
        
        # Check if user has access to this PDF
        if pdf.workspace not in request.user.profile.workspaces.all():
            if request.htmx:
                return render(request, 'partials/ai/ai_inline_qa_result.html', {
                    'error': "You don't have access to this PDF."
                })
            return JsonResponse({
                'error': "You don't have access to this PDF."
            }, status=403)
        
        # Get AI service
        ai_service = get_ai_service()
        if ai_service is None:
            if request.htmx:
                return render(request, 'partials/ai/ai_inline_qa_result.html', {
                    'error': "AI service is not configured. Please contact the administrator."
                })
            return JsonResponse({
                'error': "AI service is not configured. Please contact the administrator."
            }, status=500)
        
        # Get question from request
        question = request.POST.get('question', '').strip()
        if not question:
            if request.htmx:
                return render(request, 'partials/ai/ai_inline_qa_result.html', {
                    'error': "Please provide a question."
                })
            return JsonResponse({
                'error': "Please provide a question."
            }, status=400)
        
        # Answer question
        answer = ai_service.answer_question_about_annotations(pdf, question)
        
        if request.htmx:
            return render(request, 'partials/ai/ai_inline_qa_result.html', {
                'pdf': pdf,
                'question': question,
                'answer': answer
            })
        else:
            return JsonResponse({
                'answer': answer
            })


class AskAboutTextView(View):
    """View for asking AI about selected text in a PDF."""
    
    def post(self, request: HttpRequest, identifier: str):
        """Answer a question about selected text in a PDF."""
        import logging
        from pdf.models.pdf_models import PdfAIQuestionAnswer
        logger = logging.getLogger(__name__)
        
        logger.info(f"AskAboutTextView called with identifier: {identifier}")
        logger.info(f"POST data: {request.POST}")
        
        pdf = get_object_or_404(Pdf, id=identifier)
        
        # Check if user has access to this PDF
        if pdf.workspace not in request.user.profile.workspaces.all():
            logger.warning(f"User {request.user} does not have access to PDF {identifier}")
            return JsonResponse({
                'error': "You don't have access to this PDF."
            }, status=403)
        
        # Get AI service
        ai_service = get_ai_service()
        if ai_service is None:
            logger.error("AI service is not configured or initialized")
            return JsonResponse({
                'error': "AI service is not configured. Please contact the administrator."
            }, status=500)
        
        # Get selected text and question from request
        selected_text = request.POST.get('selected_text', '').strip()
        question = request.POST.get('question', '').strip()
        
        logger.info(f"Selected text length: {len(selected_text)}")
        logger.info(f"Selected text preview: {selected_text[:100]}...")  # Log first 100 chars
        logger.info(f"Question: {question}")
        
        if not selected_text:
            logger.warning("No text selected")
            return JsonResponse({
                'error': "No text selected."
            }, status=400)
        
        if not question:
            # If no question provided, create a default one
            question = "Please explain this text."
            logger.info("Using default question")
        
        # Create prompt for AI
        prompt = f"""
        I have selected the following text from a PDF document:
        
        "{selected_text}"
        
        Please answer the following question about this text:
        
        Question: {question}
        
        Answer:
        """
        
        logger.info("Sending request to OpenAI")
        try:
            # Ask AI about the selected text
            answer = ai_service.ask_question_with_context(prompt)
            logger.info("Received response from OpenAI")
            logger.info(f"Answer length: {len(answer)}")
            
            # Check if user wants to save this Q&A
            save_qa = request.POST.get('save_qa', False)
            if save_qa:
                # Create combined question format that matches what we parse
                # Use \n separators that our template filters expect
                combined_question = f'Q: Selected text: "{selected_text}"\nQuestion: {question}\nA: {answer}'
                
                # Save the Q&A to the database
                PdfAIQuestionAnswer.objects.create(
                    pdf=pdf,
                    page=1,  # We don't have page info for selected text, default to 1
                    text=combined_question,  # Combined text for display
                    question=combined_question,  # Store the combined format (this is what comes from frontend)
                    answer=answer,
                    creation_date=timezone.now()
                )
                logger.info("AI Q&A saved to database")
            
            return JsonResponse({
                'answer': answer
            })
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': f"Error processing request: {str(e)}"
            }, status=500)


class SaveAIQuestionAnswerView(View):
    """View for saving AI question and answer to the database."""
    
    def post(self, request: HttpRequest, identifier: str):
        """Save AI question and answer to the database."""
        import logging
        from pdf.models.pdf_models import PdfAIQuestionAnswer
        logger = logging.getLogger(__name__)
        
        logger.info(f"SaveAIQuestionAnswerView called with identifier: {identifier}")
        logger.info(f"POST data: {request.POST}")
        
        pdf = get_object_or_404(Pdf, id=identifier)
        
        # Check if user has access to this PDF
        if pdf.workspace not in request.user.profile.workspaces.all():
            logger.warning(f"User {request.user} does not have access to PDF {identifier}")
            return JsonResponse({
                'error': "You don't have access to this PDF."
            }, status=403)
        
        # Get question and answer from request
        question = request.POST.get('question', '').strip()
        answer = request.POST.get('answer', '').strip()
        
        if not question or not answer:
            logger.warning("Question or answer is missing")
            return JsonResponse({
                'error': "Both question and answer are required."
            }, status=400)
        
        # Handle case where question might already be in combined format
        actual_question = question
        combined_question = question
        
        # Check if question is already in combined format with proper separators
        if 'Selected text: "' in question and ('"\nQuestion:' in question or '"\r\nQuestion:' in question):
            # This is likely from the frontend in combined format
            # Extract the actual question part
            try:
                # Handle both \n and \r\n separators
                if '"\nQuestion:' in question:
                    question_start = question.find('"\nQuestion:') + 11
                else:  # '"\r\nQuestion:' in question
                    question_start = question.find('"\r\nQuestion:') + 12
                
                if question_start >= 11:
                    # Look for answer part
                    answer_start = question.find('\nA:', question_start)
                    if answer_start == -1:
                        answer_start = question.find('\r\nA:', question_start)
                    
                    if answer_start > question_start:
                        actual_question = question[question_start:answer_start].strip()
                    else:
                        actual_question = question[question_start:].strip()
                    combined_question = question
                else:
                    # If we can't parse it properly, use as-is and let frontend handle it
                    actual_question = question
                    combined_question = f"Q: {question}\nA: {answer}"
            except Exception as e:
                logger.warning(f"Error parsing combined question format: {str(e)}")
                # Fallback to simple format
                combined_question = f"Q: {question}\nA: {answer}"
        elif 'Selected text: "' in question and '" Question:' in question:
            # Handle the format we created in AskAboutTextView (older format)
            try:
                question_start = question.find('" Question:') + 11
                answer_start = question.find(' A:', question_start)
                if question_start >= 11:
                    if answer_start > question_start:
                        actual_question = question[question_start:answer_start].strip()
                    else:
                        actual_question = question[question_start:].strip()
                    combined_question = question
                else:
                    combined_question = f"Q: {question}\nA: {answer}"
            except Exception as e:
                logger.warning(f"Error parsing combined question format: {str(e)}")
                combined_question = f"Q: {question}\nA: {answer}"
        else:
            # Simple question/answer format - convert to our standard format
            combined_question = f"Q: {question}\nA: {answer}"
        
        try:
            # Save the Q&A to the database
            qa_entry = PdfAIQuestionAnswer.objects.create(
                pdf=pdf,
                page=1,  # We don't have page info, default to 1
                text=combined_question,  # Combined text for display
                question=combined_question,  # Store the question (in whatever format it came in)
                answer=answer,
                creation_date=timezone.now()
            )
            logger.info(f"AI Q&A saved to database with ID: {qa_entry.id}")
            
            return JsonResponse({
                'success': True,
                'message': 'AI Q&A saved successfully.'
            })
        except Exception as e:
            logger.error(f"Error saving AI Q&A: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': f"Error saving AI Q&A: {str(e)}"
            }, status=500)


class AIExtractThemesView(View):
    """View for extracting key themes from PDF annotations."""
    
    def post(self, request: HttpRequest, identifier: str):
        """Extract key themes from PDF annotations."""
        if identifier == 'all':
            # Handle overview themes for all PDFs
            pdfs = request.user.profile.current_pdfs.all()
            
            # Get AI service
            ai_service = get_ai_service()
            if ai_service is None:
                return JsonResponse({
                    'error': "AI service is not configured. Please contact the administrator."
                }, status=500)
            
            # For overview, we'll extract themes from all annotations
            all_annotations = []
            for pdf in pdfs:
                highlights = PdfHighlight.objects.filter(pdf=pdf)
                comments = PdfComment.objects.filter(pdf=pdf)
                all_annotations.extend(list(highlights) + list(comments))
            
            if not all_annotations:
                if request.htmx:
                    return render(request, 'partials/ai/ai_themes_result.html', {
                        'error': "No annotations found to analyze."
                    })
                return JsonResponse({
                    'error': "No annotations found to analyze."
                })
            
            # Extract themes for all annotations
            themes = ai_service.extract_key_themes_for_list(all_annotations)
            
            if request.htmx:
                return render(request, 'partials/ai/ai_themes_result.html', {
                    'themes': themes
                })
            else:
                return JsonResponse({
                    'themes': themes
                })
        else:
            pdf = get_object_or_404(Pdf, id=identifier)
            
            # Check if user has access to this PDF
            if pdf.workspace not in request.user.profile.workspaces.all():
                return JsonResponse({
                    'error': "You don't have access to this PDF."
                }, status=403)
            
            # Get AI service
            ai_service = get_ai_service()
            if ai_service is None:
                return JsonResponse({
                    'error': "AI service is not configured. Please contact the administrator."
                }, status=500)
            
            # Extract themes
            themes = ai_service.extract_key_themes(pdf)
            
            if request.htmx:
                return render(request, 'partials/ai/ai_themes_result.html', {
                    'pdf': pdf,
                    'themes': themes
                })
            else:
                return JsonResponse({
                    'themes': themes
                })
