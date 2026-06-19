class ApiConstants {
  static const String defaultBaseUrl = 'http://localhost:8085';
  static const Duration timeout = Duration(seconds: 30);

  // Endpoints
  static const String realPortfolio = '/api/portfolio/real';
  static const String systemPortfolio = '/api/portfolio/system';
  static const String patternsRecommended = '/api/patterns/recommended';
  static const String wishlistScan = '/api/wishlist/scan';
  static const String scanner = '/api/scan';

  // LLM Provider presets
  static const Map<String, Map<String, String>> llmProviders = {
    'openai': {
      'baseUrl': 'https://api.openai.com/v1',
      'defaultModel': 'gpt-4o',
      'apiFormat': 'openai-compatible',
    },
    'anthropic': {
      'baseUrl': 'https://api.anthropic.com',
      'defaultModel': 'claude-sonnet-4-20250514',
      'apiFormat': 'anthropic',
    },
    'openrouter': {
      'baseUrl': 'https://openrouter.ai/api/v1',
      'defaultModel': 'openrouter/auto',
      'apiFormat': 'openai-compatible',
    },
    'gemini': {
      'baseUrl': 'https://generativelanguage.googleapis.com/v1beta',
      'defaultModel': 'gemini-2.0-flash',
      'apiFormat': 'gemini',
    },
    'opencodeZen': {
      'baseUrl': '',
      'defaultModel': '',
      'apiFormat': 'openai-compatible',
    },
    'custom': {
      'baseUrl': '',
      'defaultModel': '',
      'apiFormat': 'openai-compatible',
    },
  };
}
