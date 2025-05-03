# MagMon Backend Technical Documentation

## Architecture Overview

The backend follows a layered architecture pattern:

```
backend/app/
├── api/
│   ├── routes/       # Route handlers grouped by domain
│   │   ├── games.py
│   │   ├── decks.py
│   │   └── users.py
│   ├── services/     # Business logic layer
│   │   ├── game_service.py
│   │   ├── deck_service.py
│   │   ├── user_service.py
│   │   └── profile_service.py
│   ├── schemas/      # Request/response schemas
│   │   ├── game_schemas.py
│   │   ├── deck_schemas.py
│   │   └── user_schemas.py
│   └── utils/        # Common utilities
│       ├── auth.py
│       ├── validation.py
│       └── error_handlers.py
├── models/           # Database models
└── config.py         # Application configuration
```

## Key Components

### Routes Layer
- Handles HTTP requests and responses
- Validates request data using schemas
- Delegates business logic to services
- Groups endpoints by domain (games, decks, users)

### Service Layer
- Implements business logic
- Handles database operations
- Manages file uploads and processing
- Enforces business rules and validation

### Schema Layer
- Defines request/response data structures
- Validates input data
- Ensures consistent API responses
- Documents API contracts

### Utility Layer
- Provides common functionality
- Handles authentication and authorization
- Manages error handling
- Implements validation helpers

## Authentication

- JWT-based authentication
- Token refresh mechanism
- Role-based access control
- Admin-specific endpoints

## File Handling

- Avatar uploads in `/static/uploads/avatars/`
- Secure filename generation
- File type validation
- Automatic cleanup on errors

## Error Handling

- Centralized error handlers
- Consistent error responses
- Validation error formatting
- Database error handling

## Testing

### Unit Tests
- Service layer testing
- Schema validation testing
- Utility function testing
- Mock database interactions

### Integration Tests
- API endpoint testing
- File upload testing
- Authentication flow testing
- Error handling testing

## Development Setup

1. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. Initialize database:
   ```bash
   flask db upgrade
   ```

5. Run development server:
   ```bash
   flask run
   ```

## Testing

Run tests with pytest:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app
```

## API Documentation

API documentation is available at `/api/docs` when running in development mode.

## Security Considerations

- Input validation on all endpoints
- File upload restrictions
- SQL injection prevention
- XSS protection
- CSRF protection
- Rate limiting

## Performance Optimization

- Database query optimization
- Caching strategy
- File upload size limits
- Rate limiting configuration
- Database connection pooling

## Deployment

1. Set production environment variables
2. Run database migrations
3. Configure web server (e.g., Gunicorn)
4. Set up reverse proxy (e.g., Nginx)
5. Configure SSL/TLS
6. Set up monitoring

## Maintenance

- Regular dependency updates
- Database backups
- Log rotation
- Performance monitoring
- Security audits

## Contributing

1. Follow Python style guide (PEP 8)
2. Write tests for new features
3. Update documentation
4. Use type hints
5. Follow Git workflow