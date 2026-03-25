"""
API Documentation for Fake News Detector
Provides interactive API documentation
"""

from flask import jsonify, render_template_string

API_DOCUMENTATION = {
    "info": {
        "title": "Fake News Detector API",
        "version": "1.0.0",
        "description": "API for fake news detection with Pinterest-like card grid interface",
        "contact": {
            "name": "API Support",
            "email": "support@fakenewsdetector.com"
        }
    },
    "servers": [
        {
            "url": "http://localhost:5000/api",
            "description": "Development server"
        }
    ],
    "paths": {
        "/cards": {
            "get": {
                "summary": "Get paginated news cards",
                "description": "Retrieve a paginated list of news articles with predictions",
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Page number (default: 1)",
                        "schema": {"type": "integer", "minimum": 1}
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Items per page (default: 20, max: 100)",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100}
                    },
                    {
                        "name": "search",
                        "in": "query",
                        "description": "Search query for article content or author",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "filter",
                        "in": "query",
                        "description": "Filter by prediction type",
                        "schema": {"type": "string", "enum": ["REAL", "FAKE"]}
                    },
                    {
                        "name": "sort",
                        "in": "query",
                        "description": "Sort field (default: timestamp)",
                        "schema": {"type": "string", "enum": ["timestamp", "confidence", "username"]}
                    },
                    {
                        "name": "order",
                        "in": "query",
                        "description": "Sort order (default: desc)",
                        "schema": {"type": "string", "enum": ["asc", "desc"]}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Successful response",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "cards": {
                                            "type": "array",
                                            "items": {"$ref": "#/components/schemas/NewsCard"}
                                        },
                                        "pagination": {"$ref": "#/components/schemas/Pagination"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/cards/{id}": {
            "get": {
                "summary": "Get card details",
                "description": "Retrieve detailed information about a specific news card",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "description": "Card ID",
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Card details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DetailedNewsCard"}
                            }
                        }
                    },
                    "404": {
                        "description": "Card not found"
                    }
                }
            }
        },
        "/predict": {
            "post": {
                "summary": "Analyze news article",
                "description": "Submit a news article for fake news detection",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["text"],
                                "properties": {
                                    "text": {
                                        "type": "string",
                                        "minLength": 10,
                                        "maxLength": 10000,
                                        "description": "News article text to analyze"
                                    },
                                    "source": {
                                        "type": "string",
                                        "description": "Source of the article (optional)"
                                    },
                                    "category": {
                                        "type": "string",
                                        "description": "Article category (optional)"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Prediction result",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PredictionResult"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid input"
                    },
                    "429": {
                        "description": "Rate limit exceeded"
                    }
                }
            }
        },
        "/predict/batch": {
            "post": {
                "summary": "Batch analyze articles",
                "description": "Submit multiple articles for batch analysis (max 10)",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["articles"],
                                "properties": {
                                    "articles": {
                                        "type": "array",
                                        "maxItems": 10,
                                        "items": {
                                            "type": "object",
                                            "required": ["text"],
                                            "properties": {
                                                "text": {"type": "string", "minLength": 10, "maxLength": 10000}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Batch prediction results"
                    }
                }
            }
        },
        "/cards/search": {
            "get": {
                "summary": "Search articles",
                "description": "Search for articles by content or metadata",
                "parameters": [
                    {
                        "name": "q",
                        "in": "query",
                        "required": True,
                        "description": "Search query",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "description": "Page number",
                        "schema": {"type": "integer", "minimum": 1}
                    },
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "Items per page",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Search results"
                    }
                }
            }
        },
        "/cards/stats": {
            "get": {
                "summary": "Get statistics",
                "description": "Retrieve comprehensive statistics about predictions",
                "responses": {
                    "200": {
                        "description": "Statistics data",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Statistics"}
                            }
                        }
                    }
                }
            }
        },
        "/health": {
            "get": {
                "summary": "Health check",
                "description": "Check API health status",
                "responses": {
                    "200": {
                        "description": "Health status"
                    }
                }
            }
        },
        "/model/info": {
            "get": {
                "summary": "Model information",
                "description": "Get information about the ML model",
                "responses": {
                    "200": {
                        "description": "Model information"
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "NewsCard": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "content": {"type": "string"},
                    "prediction": {"type": "string", "enum": ["REAL", "FAKE"]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "username": {"type": "string"},
                    "imageUrl": {"type": "string"},
                    "source": {"type": "string"},
                    "category": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "language": {"type": "string"},
                    "word_count": {"type": "integer"},
                    "character_count": {"type": "integer"}
                }
            },
            "DetailedNewsCard": {
                "allOf": [
                    {"$ref": "#/components/schemas/NewsCard"},
                    {
                        "type": "object",
                        "properties": {
                            "full_content": {"type": "string"},
                            "entities": {
                                "type": "object",
                                "properties": {
                                    "persons": {"type": "array", "items": {"type": "string"}},
                                    "organizations": {"type": "array", "items": {"type": "string"}},
                                    "locations": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "analysis": {
                                "type": "object",
                                "properties": {
                                    "model_version": {"type": "string"},
                                    "processed_at": {"type": "string", "format": "date-time"}
                                }
                            }
                        }
                    }
                ]
            },
            "PredictionResult": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "card": {"$ref": "#/components/schemas/NewsCard"},
                    "prediction": {
                        "type": "object",
                        "properties": {
                            "result": {"type": "string", "enum": ["REAL", "FAKE"]},
                            "confidence": {"type": "number"},
                            "probabilities": {
                                "type": "object",
                                "properties": {
                                    "REAL": {"type": "number"},
                                    "FAKE": {"type": "number"}
                                }
                            },
                            "processing_time": {"type": "number"}
                        }
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "language": {"type": "string"},
                            "entities": {"type": "object"},
                            "tags": {"type": "array", "items": {"type": "string"}},
                            "word_count": {"type": "integer"},
                            "character_count": {"type": "integer"}
                        }
                    }
                }
            },
            "Pagination": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "total_count": {"type": "integer"},
                    "total_pages": {"type": "integer"},
                    "has_more": {"type": "boolean"}
                }
            },
            "Statistics": {
                "type": "object",
                "properties": {
                    "total_predictions": {"type": "integer"},
                    "by_prediction": {
                        "type": "object",
                        "properties": {
                            "REAL": {
                                "type": "object",
                                "properties": {
                                    "count": {"type": "integer"},
                                    "avg_confidence": {"type": "number"}
                                }
                            },
                            "FAKE": {
                                "type": "object",
                                "properties": {
                                    "count": {"type": "integer"},
                                    "avg_confidence": {"type": "number"}
                                }
                            }
                        }
                    },
                    "time_based": {
                        "type": "object",
                        "properties": {
                            "last_hour": {"type": "integer"},
                            "last_24h": {"type": "integer"},
                            "last_week": {"type": "integer"},
                            "last_month": {"type": "integer"}
                        }
                    },
                    "top_tags": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "tag": {"type": "string"},
                                "count": {"type": "integer"}
                            }
                        }
                    }
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "boolean"},
                    "message": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "code": {"type": "integer"}
                }
            }
        }
    }
}

def get_api_docs():
    """Return API documentation in OpenAPI format"""
    return jsonify(API_DOCUMENTATION)

def get_api_docs_html():
    """Return HTML documentation page"""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fake News Detector API Documentation</title>
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1, h2, h3 {
                color: #333;
            }
            .endpoint {
                background: #f8f9fa;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                border-left: 4px solid #007bff;
            }
            .method {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
                font-size: 12px;
                margin-right: 10px;
            }
            .get { background: #28a745; }
            .post { background: #007bff; }
            .put { background: #ffc107; color: #333; }
            .delete { background: #dc3545; }
            .code {
                background: #f1f1f1;
                padding: 10px;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                overflow-x: auto;
            }
            .parameter {
                background: #e9ecef;
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Fake News Detector API Documentation</h1>
            <p>Welcome to the Fake News Detector API. This API provides endpoints for analyzing news articles and managing the card grid interface.</p>
            
            <h2>Base URL</h2>
            <div class="code">http://localhost:5000/api</div>
            
            <h2>Authentication</h2>
            <p>Currently, no authentication is required for API access. Rate limiting is applied to prevent abuse.</p>
            
            <h2>Rate Limits</h2>
            <ul>
                <li><strong>Prediction:</strong> 30 requests per minute</li>
                <li><strong>Batch Prediction:</strong> 5 requests per minute</li>
                <li><strong>Search:</strong> 60 requests per minute</li>
                <li><strong>General:</strong> 120 requests per minute</li>
            </ul>
            
            <h2>Endpoints</h2>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span>/cards</h3>
                <p>Retrieve paginated news cards with optional filtering and sorting.</p>
                <h4>Parameters:</h4>
                <div class="parameter">
                    <strong>page</strong> (integer, optional): Page number (default: 1)
                </div>
                <div class="parameter">
                    <strong>limit</strong> (integer, optional): Items per page (default: 20, max: 100)
                </div>
                <div class="parameter">
                    <strong>search</strong> (string, optional): Search query for content or author
                </div>
                <div class="parameter">
                    <strong>filter</strong> (string, optional): Filter by prediction type (REAL/FAKE)
                </div>
                <div class="parameter">
                    <strong>sort</strong> (string, optional): Sort field (timestamp/confidence/username)
                </div>
                <div class="parameter">
                    <strong>order</strong> (string, optional): Sort order (asc/desc)
                </div>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span>/cards/{id}</h3>
                <p>Get detailed information about a specific news card.</p>
                <h4>Parameters:</h4>
                <div class="parameter">
                    <strong>id</strong> (string, required): Card ID
                </div>
            </div>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span>/predict</h3>
                <p>Submit a news article for fake news detection.</p>
                <h4>Request Body:</h4>
                <div class="code">
{
  "text": "News article text to analyze (10-10000 characters)",
  "source": "Optional source information",
  "category": "Optional category"
}
                </div>
            </div>
            
            <div class="endpoint">
                <h3><span class="method post">POST</span>/predict/batch</h3>
                <p>Submit multiple articles for batch analysis (maximum 10 articles).</p>
                <h4>Request Body:</h4>
                <div class="code">
{
  "articles": [
    {"text": "First article text"},
    {"text": "Second article text"}
  ]
}
                </div>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span>/cards/search</h3>
                <p>Search for articles by content or metadata.</p>
                <h4>Parameters:</h4>
                <div class="parameter">
                    <strong>q</strong> (string, required): Search query
                </div>
                <div class="parameter">
                    <strong>page</strong> (integer, optional): Page number
                </div>
                <div class="parameter">
                    <strong>limit</strong> (integer, optional): Items per page
                </div>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span>/cards/stats</h3>
                <p>Get comprehensive statistics about predictions and system performance.</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span>/health</h3>
                <p>Check API health status and component availability.</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method get">GET</span>/model/info</h3>
                <p>Get information about the machine learning model.</p>
            </div>
            
            <h2>Response Format</h2>
            <p>All API responses follow a consistent format:</p>
            
            <h3>Success Response:</h3>
            <div class="code">
{
  "success": true,
  "data": { ... },
  "message": "Success",
  "timestamp": "2023-12-07T10:30:00Z"
}
            </div>
            
            <h3>Error Response:</h3>
            <div class="code">
{
  "error": true,
  "message": "Error description",
  "code": 400,
  "timestamp": "2023-12-07T10:30:00Z"
}
            </div>
            
            <h2>Example Usage</h2>
            <h3>Analyze a News Article:</h3>
            <div class="code">
curl -X POST http://localhost:5000/api/predict \\
  -H "Content-Type: application/json" \\
  -d '{"text": "Breaking news: Scientists discover new species in Amazon rainforest..."}'
            </div>
            
            <h3>Get Recent Articles:</h3>
            <div class="code">
curl "http://localhost:5000/api/cards?page=1&limit=10&sort=timestamp&order=desc"
            </div>
            
            <h3>Search Articles:</h3>
            <div class="code">
curl "http://localhost:5000/api/cards/search?q=politics&limit=5"
            </div>
            
            <h2>Error Codes</h2>
            <ul>
                <li><strong>400:</strong> Bad Request - Invalid input parameters</li>
                <li><strong>404:</strong> Not Found - Resource not found</li>
                <li><strong>405:</strong> Method Not Allowed - HTTP method not supported</li>
                <li><strong>413:</strong> Request Entity Too Large - File size exceeds limit</li>
                <li><strong>429:</strong> Too Many Requests - Rate limit exceeded</li>
                <li><strong>500:</strong> Internal Server Error - Server-side error</li>
            </ul>
            
            <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #666;">
                <p>Fake News Detector API v1.0.0 | Built with Flask and scikit-learn</p>
            </footer>
        </div>
    </body>
    </html>
    """
    return html_template