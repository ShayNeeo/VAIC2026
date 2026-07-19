import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// VAIC — SHB-inspired enterprise banking design language.
/// Institutional, intelligent, precise, modern, controlled.
/// 65% neutral white/gray, 20% navy, 10% orange, 5% semantic accents.

/// ── SHB color tokens ────────────────────────────────────────────────────────
class AppColors {
  // Brand
  static const Color navy = Color(0xFF1E245F);
  static const Color navyDark = Color(0xFF10142F);
  static const Color navySurface = Color(0xFF181D45);

  static const Color orange = Color(0xFFF36F21);
  static const Color orangeDark = Color(0xFFD95712);
  static const Color orangeLight = Color(0xFFFFF1E8);

  // Accents
  static const Color blue = Color(0xFF3E63DD);
  static const Color violet = Color(0xFF7259D9);

  // Neutrals
  static const Color background = Color(0xFFF5F7FB);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceAlt = Color(0xFFFAFBFD);
  static const Color border = Color(0xFFE2E6EF);

  static const Color textPrimary = Color(0xFF171A2E);
  static const Color textSecondary = Color(0xFF62697B);
  static const Color textDisabled = Color(0xFF9BA1B1);

  // Semantic
  static const Color success = Color(0xFF168A5B);
  static const Color warning = Color(0xFFD99100);
  static const Color error = Color(0xFFD64545);
  static const Color info = Color(0xFF3178C6);

  // ── Backwards-compatible aliases (old neon token names → SHB) ──
  static const Color ink900 = navyDark;
  static const Color ink850 = navy;
  static const Color ink800 = navySurface;
  static const Color ink700 = Color(0xFF232A5C);
  static const Color ink600 = Color(0xFF2D3570);
  static const Color line = border;
  static const Color lineSoft = border;

  static const Color cyan = orange; // CTA / active accent
  static const Color cyanSoft = orangeLight;
  static const Color magenta = violet;
  static const Color lime = success;

  static const Color ready = success;
  static const Color readyBg = Color(0xFFE8F7F0);
  static const Color needInfo = warning;
  static const Color needInfoBg = Color(0xFFFFF7DF);
  static const Color block = error;
  static const Color blockBg = Color(0xFFFDECEC);
  static const Color review = violet;
  static const Color reviewBg = Color(0xFFF2EEFC);

  static const Color txt = textPrimary;
  static const Color txt2 = textSecondary;
  static const Color muted = textDisabled;
  static const Color subtle = textSecondary;

  static const Color onSurface = textPrimary;
  static const Color primary = navy;
  static const Color secondary = violet;
  static const Color outline = border;
}

/// SHB gradients (used sparingly).
const shbPrimaryGradient = LinearGradient(
  colors: [Color(0xFF1E245F), Color(0xFF303A8C)],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);
const shbOpportunityGradient = LinearGradient(
  colors: [Color(0xFFF36F21), Color(0xFFFFA15C)],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);
const shbPremiumGradient = LinearGradient(
  colors: [Color(0xFF10142F), Color(0xFF252B68)],
  begin: Alignment.topLeft,
  end: Alignment.bottomRight,
);

/// Primary typeface — Be Vietnam Pro (Vietnamese-ready, enterprise-clean).
TextTheme _display(TextTheme base) => base.copyWith(
      displayLarge: _bv(32, FontWeight.w700, height: 1.2),
      displayMedium: _bv(28, FontWeight.w700, height: 1.25),
      displaySmall: _bv(28, FontWeight.w700, height: 1.25),
      headlineLarge: _bv(28, FontWeight.w700, height: 1.25),
      headlineMedium: _bv(22, FontWeight.w600, height: 1.3),
      headlineSmall: _bv(22, FontWeight.w600, height: 1.3),
      titleLarge: _bv(18, FontWeight.w600, height: 1.35),
      titleMedium: _bv(18, FontWeight.w600, height: 1.35),
      titleSmall: _bv(16, FontWeight.w600, height: 1.4),
      bodyLarge: _bv(16, FontWeight.w400, height: 1.5),
      bodyMedium: _bv(14, FontWeight.w400, height: 1.5),
      bodySmall: _bv(14, FontWeight.w400, height: 1.5),
      labelLarge: _bv(13, FontWeight.w600),
      labelMedium: _bv(13, FontWeight.w600),
      labelSmall: _bv(12, FontWeight.w500),
    );

TextStyle _bv(double size, FontWeight weight, {double? height}) =>
    GoogleFonts.beVietnamPro(fontSize: size, fontWeight: weight, height: height);

const TextTheme _bodyText = TextTheme(
  bodyLarge: TextStyle(fontSize: 16, fontWeight: FontWeight.w400, letterSpacing: 0.1, fontFamily: 'BeVietnamPro'),
  bodyMedium: TextStyle(fontSize: 14, fontWeight: FontWeight.w400, letterSpacing: 0.1, fontFamily: 'BeVietnamPro'),
  bodySmall: TextStyle(fontSize: 12, fontWeight: FontWeight.w400, letterSpacing: 0.2, fontFamily: 'BeVietnamPro'),
  labelLarge: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, letterSpacing: 0.1, fontFamily: 'BeVietnamPro'),
  labelMedium: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, letterSpacing: 0.3, fontFamily: 'BeVietnamPro'),
  labelSmall: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, letterSpacing: 0.4, fontFamily: 'BeVietnamPro'),
);

/// Monospace for IDs, technical logs, model outputs (tabular figures).
TextStyle get mono => GoogleFonts.jetBrainsMono(
      fontSize: 12,
      fontWeight: FontWeight.w500,
      letterSpacing: 0.2,
      color: AppColors.textSecondary,
      fontFeatures: const [FontFeature.tabularFigures()],
    );

ThemeData agentTheme(Brightness brightness) {
  final dark = brightness == Brightness.dark;
  final base = ThemeData(
    useMaterial3: true,
    brightness: brightness,
    colorScheme: dark
        ? ColorScheme.dark(
            primary: AppColors.orange,
            onPrimary: Colors.white,
            secondary: AppColors.violet,
            error: AppColors.error,
            surface: AppColors.navySurface,
            onSurface: Colors.white,
            outline: AppColors.border,
            brightness: brightness,
          )
        : ColorScheme.light(
            primary: AppColors.navy,
            onPrimary: Colors.white,
            secondary: AppColors.violet,
            error: AppColors.error,
            surface: AppColors.surface,
            onSurface: AppColors.textPrimary,
            outline: AppColors.border,
            brightness: brightness,
          ),
    scaffoldBackgroundColor: dark ? AppColors.navyDark : AppColors.background,
    fontFamily: GoogleFonts.beVietnamPro().fontFamily,
    textTheme: _display(
      (dark ? ThemeData.dark() : ThemeData.light()).textTheme.apply(
            bodyColor: dark ? Colors.white : AppColors.textPrimary,
            displayColor: dark ? Colors.white : AppColors.textPrimary,
          ),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.orange,
        foregroundColor: Colors.white,
        elevation: 0,
        shadowColor: AppColors.orange.withValues(alpha: 0.3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
        textStyle: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w700, fontSize: 13, letterSpacing: 0.2),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: dark ? Colors.white : AppColors.navy,
        side: BorderSide(color: dark ? AppColors.navySurface : AppColors.border),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.orange,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        textStyle: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w700, fontSize: 13),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: dark ? AppColors.navySurface : AppColors.surface,
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide(color: dark ? AppColors.navySurface : AppColors.border)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: BorderSide(color: dark ? AppColors.navySurface : AppColors.border)),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: AppColors.orange, width: 2),
      ),
      errorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(8), borderSide: const BorderSide(color: AppColors.error)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      labelStyle: TextStyle(color: dark ? Colors.white70 : AppColors.textSecondary, fontFamily: 'BeVietnamPro'),
      hintStyle: TextStyle(color: dark ? Colors.white38 : AppColors.textDisabled, fontFamily: 'BeVietnamPro'),
    ),
    cardTheme: CardThemeData(
      color: dark ? AppColors.navySurface : AppColors.surface,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: dark ? AppColors.navySurface : AppColors.border),
      ),
      margin: const EdgeInsets.all(0),
    ),
    dividerTheme: DividerThemeData(color: dark ? AppColors.navySurface : AppColors.border, thickness: 1, space: 1),
    chipTheme: ChipThemeData(
      backgroundColor: dark ? AppColors.navySurface : AppColors.orangeLight,
      side: BorderSide(color: dark ? AppColors.navySurface : AppColors.border),
      labelStyle: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: dark ? Colors.white : AppColors.textSecondary, fontFamily: 'BeVietnamPro'),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
    ),
  );
  return base;
}

ThemeData lightAgentTheme() => agentTheme(Brightness.light);
