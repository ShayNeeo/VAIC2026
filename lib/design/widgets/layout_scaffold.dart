import 'package:flutter/material.dart';
import '../theme/responsive.dart';

/// Main layout scaffold — 3-col desktop (sidebar + main + drawer) / stacked mobile
class LayoutScaffold extends StatelessWidget {
  final Widget sidebar;
  final Widget body;
  final Widget? endDrawer;
  final PreferredSizeWidget? appBar;
  final FloatingActionButton? floatingActionButton;

  const LayoutScaffold({
    super.key,
    required this.sidebar,
    required this.body,
    this.endDrawer,
    this.appBar,
    this.floatingActionButton,
  });

  @override
  Widget build(BuildContext context) {
    return ResponsiveBuilder(
      builder: (context, size) {
        if (size == ScreenSize.mobile || size == ScreenSize.tablet) {
          return _MobileLayout(
            sidebar: sidebar,
            body: body,
            endDrawer: endDrawer,
            appBar: appBar,
            floatingActionButton: floatingActionButton,
          );
        }
        return _DesktopLayout(
          sidebar: sidebar,
          body: body,
          endDrawer: endDrawer,
          appBar: appBar,
        );
      },
    );
  }
}

class _DesktopLayout extends StatelessWidget {
  final Widget sidebar;
  final Widget body;
  final Widget? endDrawer;
  final PreferredSizeWidget? appBar;

  const _DesktopLayout({
    required this.sidebar,
    required this.body,
    this.endDrawer,
    this.appBar,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      endDrawer: endDrawer,
      body: Row(
        children: [
          // Sidebar (280px fixed)
          SizedBox(
            width: 280,
            child: Container(
              color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
              child: sidebar,
            ),
          ),
          const VerticalDivider(width: 1, thickness: 1),
          // Main content (flexible)
          Expanded(
            child: body,
          ),
        ],
      ),
    );
  }
}

class _MobileLayout extends StatelessWidget {
  final Widget sidebar;
  final Widget body;
  final Widget? endDrawer;
  final PreferredSizeWidget? appBar;
  final FloatingActionButton? floatingActionButton;

  const _MobileLayout({
    required this.sidebar,
    required this.body,
    this.endDrawer,
    this.appBar,
    this.floatingActionButton,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: appBar,
      drawer: Drawer(
        child: SafeArea(child: sidebar),
      ),
      endDrawer: endDrawer,
      floatingActionButton: floatingActionButton,
      body: body,
    );
  }
}

/// Three-column desktop layout for Decision Workspace (S2)
/// Left: Context + Need Summary | Center: Opportunity Cards | Right: Evidence/Action
class ThreeColumnLayout extends StatelessWidget {
  final Widget left;
  final Widget center;
  final Widget right;
  final double leftWidth;
  final double rightWidth;

  const ThreeColumnLayout({
    super.key,
    required this.left,
    required this.center,
    required this.right,
    this.leftWidth = 360,
    this.rightWidth = 360,
  });

  @override
  Widget build(BuildContext context) {
    return ResponsiveBuilder(
      builder: (context, size) {
        if (size == ScreenSize.mobile) {
          return _MobileStacked(left: left, center: center, right: right);
        }
        if (size == ScreenSize.tablet) {
          return _TabletLayout(left: left, center: center, right: right);
        }
        return _DesktopThreeCol(
          left: left,
          center: center,
          right: right,
          leftWidth: leftWidth,
          rightWidth: rightWidth,
        );
      },
    );
  }
}

class _DesktopThreeCol extends StatelessWidget {
  final Widget left;
  final Widget center;
  final Widget right;
  final double leftWidth;
  final double rightWidth;

  const _DesktopThreeCol({
    required this.left,
    required this.center,
    required this.right,
    required this.leftWidth,
    required this.rightWidth,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Left panel
        SizedBox(
          width: leftWidth,
          child: Container(
            color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
            child: SingleChildScrollView(child: left),
          ),
        ),
        const VerticalDivider(width: 1),
        // Center (flexible)
        Expanded(
          child: SingleChildScrollView(child: center),
        ),
        const VerticalDivider(width: 1),
        // Right panel
        SizedBox(
          width: rightWidth,
          child: Container(
            color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
            child: SingleChildScrollView(child: right),
          ),
        ),
      ],
    );
  }
}

class _TabletLayout extends StatelessWidget {
  final Widget left;
  final Widget center;
  final Widget right;

  const _TabletLayout({required this.left, required this.center, required this.right});

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(flex: 2, child: SingleChildScrollView(child: left)),
        const VerticalDivider(width: 1),
        Expanded(flex: 3, child: SingleChildScrollView(child: center)),
      ],
    );
  }
}

class _MobileStacked extends StatelessWidget {
  final Widget left;
  final Widget center;
  final Widget right;

  const _MobileStacked({required this.left, required this.center, required this.right});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [left, const Divider(), center, const Divider(), right],
      ),
    );
  }
}