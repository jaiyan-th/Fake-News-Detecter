const API_BASE_URL = window.location.protocol.startsWith('http')
    ? `${window.location.protocol}//${window.location.hostname}:${window.location.port}`
    : 'http://localhost:3000';

class ApiService {
    async register(email, password, name) {
        return this._authRequest('/api/auth/register', { email, password, name });
    }

    async login(email, password) {
        return this._authRequest('/api/auth/login', { email, password });
    }

    async logout() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'  // Include cookies for session
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear any local storage or session data
                return { success: true };
            } else {
                return { success: false, error: data.error || 'Logout failed' };
            }
        } catch (error) {
            console.error('Logout error:', error);
            // Even if logout fails on server, clear client-side state
            return { success: true };
        }
    }

    async getCurrentUser() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
                method: 'GET',
                credentials: 'include'
            });
            
            if (response.ok) {
                const data = await response.json();
                return data;
            }
            return { success: false };
        } catch (error) {
            console.error('Get user error:', error);
            return { success: false };
        }
    }

    async changePassword(currentPassword, newPassword) {
        return this._authRequest('/api/auth/change-password', { 
            current_password: currentPassword, 
            new_password: newPassword 
        });
    }

    async initiateGoogleOAuth() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/google`, {
                method: 'GET',
                credentials: 'include'
            });
            
            const data = await response.json();
            
            if (data.success && data.authorization_url) {
                // Redirect to Google OAuth
                window.location.href = data.authorization_url;
            } else {
                return { success: false, error: data.error || 'OAuth initialization failed' };
            }
        } catch (error) {
            console.error('OAuth error:', error);
            return { success: false, error: error.message };
        }
    }

    async analyzeText(text) {
        return this._request('/analyze-text', { text });
    }

    async analyzeUrl(url) {
        return this._request('/analyze-url', { url });
    }

    async analyzeImage(file) {
        const formData = new FormData();
        formData.append('image', file);
        
        try {
            const response = await fetch(`${API_BASE_URL}/analyze-image`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                return {
                    success: true,
                    prediction: data.verdict,
                    confidence: parseFloat(data.confidence.replace('%', '')) / 100,
                    explanation: data.explanation,
                    domain: 'OCR Analysis',
                    verified_sources: data.matched_articles || [],
                    processing_time: data.processing_time,
                    extracted_text: data.extracted_text || '',
                    llm_analysis: {
                        enabled: false,
                        summary: data.explanation
                    },
                    input_type: 'image'
                };
            } else {
                return {
                    success: false,
                    error: data.error || 'Image analysis failed'
                };
            }
        } catch (error) {
            console.error('API Error:', error);
            return { 
                success: false, 
                error: error.message || 'Network error occurred'
            };
        }
    }

    async getHistory(page = 1, perPage = 20) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/history/?page=${page}&per_page=${perPage}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Transform backend format to frontend format
            const transformedAnalyses = data.analyses.map(analysis => ({
                id: analysis.id,
                input_type: analysis.input_type,
                input_text: analysis.input_preview,
                prediction: analysis.verdict,
                confidence: analysis.confidence / 100, // Convert percentage to decimal
                domain: analysis.input_type === 'url' ? 'URL Analysis' : 'Text Analysis',
                timestamp: analysis.created_at
            }));
            
            return {
                success: true,
                history: transformedAnalyses,
                total: data.total,
                page: data.page,
                pages: data.pages
            };
        } catch (error) {
            console.error('Get history error:', error);
            return { 
                success: false, 
                error: error.message,
                history: [] 
            };
        }
    }

    async getHistoryStats() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/history/stats`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Get stats error:', error);
            return { 
                success: false,
                error: error.message,
                total_analyses: 0,
                verdict_distribution: {},
                average_confidence: 0
            };
        }
    }

    async deleteAnalysis(analysisId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/history/${analysisId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Delete analysis error:', error);
            return { 
                success: false,
                error: error.message
            };
        }
    }

    async clearHistory() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/history/clear`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Clear history error:', error);
            return { 
                success: false,
                error: error.message
            };
        }
    }

    async _authRequest(endpoint, body, method = 'POST') {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',  // Include cookies for session
                body: method !== 'GET' ? JSON.stringify(body) : undefined
            });
            
            const data = await response.json();
            return data;
            
        } catch (error) {
            console.error('Auth API Error:', error);
            return { 
                success: false, 
                error: error.message || 'Network error occurred'
            };
        }
    }

    async _request(endpoint, body) {
        try {
            console.log(`API Request to ${endpoint}:`, body);
            
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'frontend-client-key'  // Add API key for authentication
                },
                credentials: 'include',  // Include cookies for session
                body: JSON.stringify(body)
            });
            
            const data = await response.json();
            console.log(`API Response from ${endpoint}:`, data);
            
            if (response.ok) {
                // Determine input type from endpoint
                let inputType = 'text';
                if (endpoint.includes('url')) {
                    inputType = 'url';
                } else if (endpoint.includes('image')) {
                    inputType = 'image';
                }
                
                // Parse confidence - handle both "85%" string and 0.85 number formats
                let confidenceValue;
                if (typeof data.confidence === 'string') {
                    confidenceValue = parseFloat(data.confidence.replace('%', '')) / 100;
                } else if (typeof data.confidence === 'number') {
                    confidenceValue = data.confidence > 1 ? data.confidence / 100 : data.confidence;
                } else {
                    confidenceValue = 0.5; // Default fallback
                }
                
                // Transform backend response to frontend format
                return {
                    success: true,
                    prediction: data.verdict || 'UNCERTAIN',
                    confidence: confidenceValue,
                    explanation: data.explanation || 'Analysis completed',
                    domain: 'News Analysis',
                    verified_sources: data.matched_articles || [],
                    processing_time: data.processing_time || 0,
                    input_type: inputType,
                    llm_analysis: {
                        enabled: true,
                        provider: 'Groq Multi-Model',
                        model: 'Llama 3 Ensemble (8B + 90B + 70B)',
                        summary: data.explanation || 'No summary available',
                        verdict: data.verdict || 'UNCERTAIN',
                        reasoning: []
                    }
                };
            } else {
                console.error('API Error Response:', data);
                return {
                    success: false,
                    error: data.error || 'Analysis failed'
                };
            }
        } catch (error) {
            console.error('API Error:', error);
            return { 
                success: false, 
                error: error.message || 'Network error occurred'
            };
        }
    }
}

const api = new ApiService();
