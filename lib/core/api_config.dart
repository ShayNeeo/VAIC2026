import 'api_client.dart';

/// Runtime backend configuration.
///
/// Defaults to the deployed backend (vaic-api.w9.nu). Override for local
/// dev with: flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'https://vaic-api.w9.nu',
);

ApiClient buildApiClient() => ApiClient(baseUrl: kApiBaseUrl);
