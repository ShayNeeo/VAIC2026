import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// VAIC — Agent OS design language.
/// Dark glassmorphism, neon cyan/violet, AI-stream accents.
/// No bundled "normal" fonts: distinctive display/body/mono faces
/// pulled from Google Fonts at runtime (Space Grotesk / Hanken Grotesk / JetBrains Mono).

class AppColors {
  // Base canvas — deep space navy
  static const Color ink900 = Color(0xFF05070E);
  static const Color ink850 = Color(0xFF080B16);
  static const Color ink800 = Color(0xFF0C1120);
  static const Color ink700 = Color(0xFF121A2E);
  static const Color ink600 = Color(0xFF1A2540);
  static const Color line = Color(0xFF243154);
  static const Color lineSoft = Color(0xFF1A2440);

  // Neon accents — AI agent glow
  static const Color cyan = Color(0xFF26E6F0);
  static const Color cyanSoft = Color(0xFF7DF2FF);
  static const Color violet = Color(0xFF8B5CF6);
  static const Color violetSoft = Color(0xFFC4B5FD);
  static const Color magenta = Color(0xFFE553C9);
  static const Color lime = Color(0xFF56F0B0);

  // Semantic status (banking-grade, per brief §12)
  static const Color ready = Color(0xFF35D6A0);
  static const Color readyBg = Color(0xFF0E2A22);
  static const Color needInfo = Color(0xFFE0A93C);
  static const Color needInfoBg = Color(0xFF2A2110);
  static const Color block = Color(0xFFF0566B);
  static const Color blockBg = Color(0xFF2E1119);
  static const Color review = Color(0xFF9B7BF0);
  static const Color reviewBg = Color(0xFF1A1640);

  // Text
  static const Color txt = Color(0xFFF2F6FF);
  static const Color txt2 = Color(0xFFB9C4DC);
  static const Color muted = Color(0xFF7A88A8);
  static const Color subtle = Color(0xFF566183);

  static const Color onSurface = Color(0xFFF2F6FF);
  static const Color surface = Color(0xFF0E1424);
  static const Color background = Color(0xFF05070E);
  static const Color primary = Color(0xFF26E6F0);
  static const Color secondary = Color(0xFF8B5CF6);
  static const Color error = Color(0xFFF0566B);
  static const Color outline = Color(0xFF243154);
}

/// Display + heading face.
TextTheme _display(TextTheme base) => base.copyWith(
      displayLarge: base.displayLarge!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w700, letterSpacing: -1.5),
      displayMedium: base.displayMedium!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w700, letterSpacing: -1.0),
      displaySmall: base.displaySmall!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w600, letterSpacing: -0.5),
      headlineLarge: base.headlineLarge!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w700, letterSpacing: -0.8),
      headlineMedium: base.headlineMedium!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w600, letterSpacing: -0.5),
      headlineSmall: base.headlineSmall!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w600),
      titleLarge: base.titleLarge!.copyWith(fontFamily: 'Space Grotesk', fontWeight: FontWeight.w600, letterSpacing: 0),
      titleMedium: base.titleMedium!.copyWith(fontFamily: 'Hanken Grotesk', fontWeight: FontWeight.w600),
      titleSmall: base.titleSmall!.copyWith(fontFamily: 'Hanken Grotesk', fontWeight: FontWeight.w600),
    );

const TextTheme _bodyText = TextTheme(
  bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.1, fontFamily: 'Hanken Grotesk'),
  bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, letterSpacing: 0.1, fontFamily: 'Hanken Grotesk'),
  bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, letterSpacing: 0.2, fontFamily: 'Hanken Grotesk'),
  labelLarge: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, letterSpacing: 0.1, fontFamily: 'Hanken Grotesk'),
  labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.3, fontFamily: 'Hanken Grotesk'),
  labelSmall: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.4, fontFamily: 'Hanken Grotesk'),
);

/// Monospace face for data, IDs, trace hashes, code.
TextStyle get mono => GoogleFonts.jetBrainsMono(
      fontSize: 12,
      fontWeight: FontWeight.w500,
      letterSpacing: 0.2,
      color: AppColors.txt2,
    );

ThemeData agentTheme(Brightness brightness) {
  final base = ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: ColorScheme.dark(
      primary: AppColors.cyan,
      onPrimary: AppColors.ink900,
      secondary: AppColors.violet,
      error: AppColors.block,
      surface: AppColors.surface,
      onSurface: AppColors.txt,
      outline: AppColors.line,
      brightness: brightness,
    ),
    scaffoldBackgroundColor: AppColors.background,
    fontFamily: 'Hanken Grotesk',
    textTheme: _display(_bodyText),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.cyan,
        foregroundColor: AppColors.ink900,
        elevation: 0,
        shadowColor: AppColors.cyan.withValues(alpha: 0.5),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 13),
        textStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, letterSpacing: 0.2, fontFamily: 'Hanken Grotesk'),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.txt,
        side: const BorderSide(color: AppColors.line),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 13),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.cyan,
        foregroundColor: AppColors.ink900,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        textStyle: const TextStyle(fontWeight: FontWeight.w800, fontSize: 13, fontFamily: 'Hanken Grotesk'),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.ink800,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.line)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.line)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: AppColors.cyan, width: 2),
      ),
      errorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.block)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
      labelStyle: const TextStyle(color: AppColors.muted, fontFamily: 'Hanken Grotesk'),
      hintStyle: const TextStyle(color: AppColors.subtle, fontFamily: 'Hanken Grotesk'),
    ),
    cardTheme: CardThemeData(
      color: AppColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18), side: const BorderSide(color: AppColors.lineSoft)),
      margin: const EdgeInsets.all(0),
    ),
    dividerTheme: const DividerThemeData(color: AppColors.lineSoft, thickness: 1, space: 1),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.ink700,
      side: const BorderSide(color: AppColors.line),
      labelStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: AppColors.txt2, fontFamily: 'Hanken Grotesk'),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
    ),
  );
  return base;
}

ThemeData lightAgentTheme() => agentTheme(Brightness.light).copyWith(
      colorScheme: ColorScheme.light(
        primary: AppColors.cyan,
        onPrimary: AppColors.ink900,
        secondary: AppColors.violet,
        error: AppColors.block,
        surface: const Color(0xFFF4F7FD),
        onSurface: const Color(0xFF0A1020),
        outline: const Color(0xFFD7E0F0),
      ),
      scaffoldBackgroundColor: const Color(0xFFEEF3FB),
      textTheme: _display(_bodyText.apply(bodyColor: const Color(0xFF0A1020), displayColor: const Color(0xFF0A1020))),
      cardTheme: CardThemeData(
        color: const Color(0xFFFFFFFF),
        elevation: 0,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18), side: const BorderSide(color: Color(0xFFD7E0F0))),
        margin: const EdgeInsets.all(0),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: const Color(0xFFFFFFFF),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Color(0xFFD7E0F0))),
        enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: Color(0xFFD7E0F0))),
        focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.cyan, width: 2)),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
      ),
    );
