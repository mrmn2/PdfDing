# PdfDing Docker Compose Configuration

This directory contains Docker Compose files for running PdfDing in different configurations.

## Available Compose Files

1. **postgres.docker-compose.yaml** - For production use with PostgreSQL database
2. **sqlite.docker-compose.yaml** - For quick testing with SQLite database (uses pre-built image)
3. **local-build.yml** - For local development (builds from source code)

## Environment Configuration

All compose files are configured to use the `.env` file located in the project root directory.

Make sure your `.env` file contains the necessary configuration, especially:
- OPENAI_API_KEY (required for AI features)
- Other optional settings as needed

## Running PdfDing

### For local development (recommended):
```bash
cd compose
docker-compose -f local-build.yml up --build
```

### For PostgreSQL database:
```bash
cd compose
docker-compose -f postgres.docker-compose.yaml up --build
```

### For SQLite database (quick testing):
```bash
cd compose
docker-compose -f sqlite.docker-compose.yaml up
```

## Stopping the Services

```bash
# Press Ctrl+C in the terminal, or run:
docker-compose -f [compose-file-name] down
```

## Debugging

The compose files are configured with `LOG_LEVEL=INFO` to show detailed logging information.
If you need more verbose logging, you can change this to `DEBUG` in the compose files.
