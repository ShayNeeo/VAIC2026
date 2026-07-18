import 'api_client.dart';

/// Runtime backend configuration.
///
/// Default points at the future production domain `vaic-api.w9.nu`.
/// While developing against a local Cloudflare tunnel, override with:
///   flutter run --dart-define=API_BASE_URL=https://<tunnel>.trycloudflare.com
const String kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: kDefaultBaseUrl,
);

ApiClient buildApiClient() => ApiClient(baseUrl: kApiBaseUrl);
