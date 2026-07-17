import 'package:flutter/material.dart';

/// App color scheme matching SHB Opportunity OS reference (mobile/index.html)
class AppColors {
  // Brand
  static const Color navy950 = Color(0xFF06172D);
  static const Color navy900 = Color(0xFF071A33);
  static const Color navy800 = Color(0xFF0E2F57);
  static const Color navy700 = Color(0xFF164778);
  static const Color blue = Color(0xFF2D7Bdd);
  static const Color blue100 = Color(0xFFE9F2FF);
  static const Color orange = Color(0xFFED6B1A);
  static const Color orange700 = Color(0xFFC94F0D);
  static const Color orange100 = Color(0xFFFFF0E6);

  // Status colors (semantic, per brief §12)
  static const Color statusReady = Color(0xFF17875B);      // xanh - ready
  static const Color statusReady100 = Color(0xFFE7F7EF);
  static const Color statusNeedInfo = Color(0xFFA26B00);   // vàng - missing info
  static const Color statusNeedInfo100 = Color(0xFFFFF4D6);
  static const Color statusBlocked = Color(0xFFB93232);    // đỏ - blocked/review
  static const Color statusBlocked100 = Color(0xFFFDEAEA);
  static const Color statusAiCta = Color(0xFF637083);      // xám - AI CTA
  static const Color statusAiCta100 = Color(0xFFEEF2F7);

  // Neutral palette
  static const Color surface = Color(0xFFFFFFFF);
  static const Color background = Color(0xFFF3F6FA);
  static const Color ink = Color(0xFF111827);
  static const Color ink2 = Color(0xFF253247);
  static const Color muted = Color(0xFF637083);
  static const Color subtle = Color(0xFF8C98A8);
  static const Color line = Color(0xFFDDE4EC);
  static const Color onSurface = Color(0xFF111827);
  static const Color onPrimary = Color(0xFFFFFFFF);
  static const Color primary = Color(0xFF071A33);          // navy
  static const Color primaryContainer = Color(0xFFE9F2FF);
  static const Color secondary = Color(0xFF637083);
  static const Color error = Color(0xFFB93232);
  static const Color outline = Color(0xFFDDE4EC);
}

/// Light theme — SHB Opportunity OS look (navy + orange)
ThemeData lightTheme() => ThemeData(
  useMaterial3: true,
  brightness: Brightness.light,
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.navy900,
    brightness: Brightness.light,
    primary: AppColors.navy900,
    onPrimary: AppColors.onPrimary,
    primaryContainer: AppColors.blue100,
    secondary: AppColors.blue,
    error: AppColors.error,
    surface: AppColors.surface,
    onSurface: AppColors.ink,
    outline: AppColors.line,
  ),
  scaffoldBackgroundColor: AppColors.background,
  fontFamily: 'Inter',
  textTheme: _textTheme,
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.orange,
      foregroundColor: AppColors.onPrimary,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      textStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: AppColors.ink2,
      side: BorderSide(color: AppColors.line),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: AppColors.surface,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(13),
      borderSide: BorderSide(color: AppColors.line),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(13),
      borderSide: BorderSide(color: AppColors.line),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(13),
      borderSide: BorderSide(color: AppColors.blue, width: 2),
    ),
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
  ),
  cardTheme: CardThemeData(
    color: AppColors.surface,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16),
      side: BorderSide(color: AppColors.line),
    ),
    margin: const EdgeInsets.all(0),
  ),
  dividerTheme: const DividerThemeData(
    color: AppColors.line,
    thickness: 1,
    space: 1,
  ),
);

/// Dark theme
ThemeData darkTheme() => ThemeData(
  useMaterial3: true,
  brightness: Brightness.dark,
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.navy900,
    brightness: Brightness.dark,
    primary: AppColors.navy700,
    onPrimary: AppColors.onPrimary,
    primaryContainer: const Color(0xFF1E3A5F),
    secondary: AppColors.blue,
    error: const Color(0xFFFFB4AB),
    surface: const Color(0xFF161E29),
    onSurface: const Color(0xFFFFFFFF),
    outline: const Color(0xFF333A47),
  ),
  scaffoldBackgroundColor: const Color(0xFF0C141F),
  fontFamily: 'Inter',
  textTheme: _textTheme.apply(bodyColor: Colors.white, displayColor: Colors.white),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: AppColors.orange,
      foregroundColor: AppColors.onPrimary,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      textStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 13),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: Colors.white,
      side: BorderSide(color: const Color(0xFF333A47)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(11)),
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: const Color(0xFF161E29),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(13),
      borderSide: const BorderSide(color: Color(0xFF333A47)),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(13),
      borderSide: const BorderSide(color: Color(0xFF333A47)),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(13),
      borderSide: const BorderSide(color: AppColors.blue, width: 2),
    ),
    contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
  ),
  cardTheme: CardThemeData(
    color: const Color(0xFF161E29),
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16),
      side: const BorderSide(color: Color(0xFF333A47)),
    ),
    margin: const EdgeInsets.all(0),
  ),
  dividerTheme: const DividerThemeData(
    color: Color(0xFF333A47),
    thickness: 1,
    space: 1,
  ),
);

/// Shared text theme (Inter-like system font fallback)
const TextTheme _textTheme = TextTheme(
  displayLarge: TextStyle(fontSize: 57, fontWeight: FontWeight.w400, letterSpacing: -0.25),
  displayMedium: TextStyle(fontSize: 45, fontWeight: FontWeight.w400),
  displaySmall: TextStyle(fontSize: 36, fontWeight: FontWeight.w400),
  headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.w600, letterSpacing: 0.0),
  headlineMedium: TextStyle(fontSize: 28, fontWeight: FontWeight.w600, letterSpacing: 0.0),
  headlineSmall: TextStyle(fontSize: 24, fontWeight: FontWeight.w600, letterSpacing: 0.0),
  titleLarge: TextStyle(fontSize: 22, fontWeight: FontWeight.w500, letterSpacing: 0.0),
  titleMedium: TextStyle(fontSize: 16, fontWeight: FontWeight.w500, letterSpacing: 0.15),
  titleSmall: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, letterSpacing: 0.1),
  bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.5),
  bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, letterSpacing: 0.25),
  bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, letterSpacing: 0.4),
  labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, letterSpacing: 0.1),
  labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w500, letterSpacing: 0.5),
  labelSmall: TextStyle(fontSize: 11, fontWeight: FontWeight.w500, letterSpacing: 0.5),
);