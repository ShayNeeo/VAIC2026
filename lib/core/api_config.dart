import 'api_client.dart';

/// Runtime backend configuration.
///
/// Android emulator reaches the local backend through 10.0.2.2.
/// For a physical phone, pass a LAN IP or tunnel URL:
///   flutter run --dart-define=API_BASE_URL=http://192.168.1.10:8000
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

ApiClient buildApiClient() => ApiClient(baseUrl: kApiBaseUrl);
