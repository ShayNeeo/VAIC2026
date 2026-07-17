import 'package:flutter/material.dart';

/// Breakpoints for responsive layouts per brief §12 (desktop 3-col / mobile stacked)
class Breakpoints {
  static const double mobile = 600;
  static const double tablet = 900;
  static const double desktop = 1200;
  static const double wide = 1600;
}

/// Screen size enum
enum ScreenSize { mobile, tablet, desktop, wide }

/// Determine screen size from width
ScreenSize getScreenSize(double width) {
  if (width < Breakpoints.mobile) return ScreenSize.mobile;
  if (width < Breakpoints.tablet) return ScreenSize.tablet;
  if (width < Breakpoints.desktop) return ScreenSize.desktop;
  return ScreenSize.wide;
}

/// Responsive builder widget — chooses layout based on width
class ResponsiveBuilder extends StatelessWidget {
  final Widget Function(BuildContext, ScreenSize) builder;
  const ResponsiveBuilder({super.key, required this.builder});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final size = getScreenSize(constraints.maxWidth);
        return builder(context, size);
      },
    );
  }
}

/// Helper: returns true if desktop or wider
bool isDesktop(BuildContext context) {
  final width = MediaQuery.of(context).size.width;
  return width >= Breakpoints.desktop;
}

/// Helper: returns true if mobile
bool isMobile(BuildContext context) {
  final width = MediaQuery.of(context).size.width;
  return width < Breakpoints.tablet;
}

/// Responsive value — different values per breakpoint
T responsiveValue<T>(BuildContext context, {
  required T mobile,
  T? tablet,
  T? desktop,
  T? wide,
}) {
  final size = getScreenSize(MediaQuery.of(context).size.width);
  switch (size) {
    case ScreenSize.mobile:
      return mobile;
    case ScreenSize.tablet:
      return tablet ?? mobile;
    case ScreenSize.desktop:
      return desktop ?? tablet ?? mobile;
    case ScreenSize.wide:
      return wide ?? desktop ?? tablet ?? mobile;
  }
}

/// Responsive padding
EdgeInsets responsivePadding(BuildContext context) {
  final size = getScreenSize(MediaQuery.of(context).size.width);
  switch (size) {
    case ScreenSize.mobile:
      return const EdgeInsets.all(16);
    case ScreenSize.tablet:
      return const EdgeInsets.all(24);
    case ScreenSize.desktop:
      return const EdgeInsets.symmetric(horizontal: 32, vertical: 24);
    case ScreenSize.wide:
      return const EdgeInsets.symmetric(horizontal: 48, vertical: 32);
  }
}

/// Responsive grid columns
int gridColumns(BuildContext context) {
  final size = getScreenSize(MediaQuery.of(context).size.width);
  switch (size) {
    case ScreenSize.mobile:
      return 1;
    case ScreenSize.tablet:
      return 2;
    case ScreenSize.desktop:
      return 3;
    case ScreenSize.wide:
      return 4;
  }
}