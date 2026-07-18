import 'package:flutter/material.dart';
import 'package:animations/animations.dart';
import 'package:shimmer/shimmer.dart';
import '../theme/app_theme.dart';

/// ── Agent OS building blocks ──────────────────────────────────────────────
/// Dark-glass, neon-glow UI primitives. All screens compose from these.

/// Animated AI mesh backdrop — drifting cyan/violet blobs over deep space.
class AgentMeshBackground extends StatefulWidget {
  final Widget child;
  final bool showGrid;
  const AgentMeshBackground({super.key, required this.child, this.showGrid = true});

  @override
  State<AgentMeshBackground> createState() => _AgentMeshBackgroundState();
}

class _AgentMeshBackgroundState extends State<AgentMeshBackground>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(seconds: 18))..repeat(reverse: true);

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Positioned.fill(child: Container(color: AppColors.background)),
        AnimatedBuilder(
          animation: _c,
          builder: (_, __) => Stack(
            children: [
              _blob(AppColors.cyan.withValues(alpha: 0.16), 0.30, -0.2 + _c.value * 0.5, 0.1 + _c.value * 0.3, 380),
              _blob(AppColors.violet.withValues(alpha: 0.16), 0.7 + _c.value * 0.3, 0.5, 0.7 - _c.value * 0.4, 420),
              _blob(AppColors.magenta.withValues(alpha: 0.10), 0.1, 0.6, 0.2 + _c.value * 0.4, 300),
            ],
          ),
        ),
        if (widget.showGrid)
          Opacity(
            opacity: 0.4,
            child: CustomPaint(size: Size.infinite, painter: _GridPainter()),
          ),
        Positioned.fill(child: widget.child),
      ],
    );
  }

  Widget _blob(Color c, double left, double top, double right, double size) => Positioned(
        left: left * MediaQuery.of(context).size.width,
        top: top * MediaQuery.of(context).size.height,
        right: right * MediaQuery.of(context).size.width,
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(color: c, shape: BoxShape.circle, boxShadow: [BoxShadow(color: c, blurRadius: 120, spreadRadius: -20)]),
        ),
      );
}

class _GridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()..color = AppColors.lineSoft.withValues(alpha: 0.5)..strokeWidth = 1;
    const step = 48.0;
    for (double x = 0; x < size.width; x += step) {
      canvas.drawLine(Offset(x, 0), Offset(x, size.height), paint);
    }
    for (double y = 0; y < size.height; y += step) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}

/// Frosted-glass surface with neon hairline border.
class GlassCard extends StatelessWidget {
  final Widget child;
  final EdgeInsetsGeometry padding;
  final double radius;
  final Color? glow;
  final bool border;
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(18),
    this.radius = 18,
    this.glow,
    this.border = true,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.72),
        borderRadius: BorderRadius.circular(radius),
        border: border ? Border.all(color: (glow ?? cs.outline).withValues(alpha: 0.6)) : null,
        boxShadow: [
          if (glow != null) BoxShadow(color: glow!.withValues(alpha: 0.18), blurRadius: 30, offset: const Offset(0, 8)),
        ],
      ),
      child: child,
    );
  }
}

/// Neon gradient pill used for brand + section acccents.
class NeonPill extends StatelessWidget {
  final Widget child;
  final List<Color> colors;
  const NeonPill({super.key, required this.child, this.colors = const [AppColors.cyan, AppColors.violet]});

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: colors),
          borderRadius: BorderRadius.circular(999),
          boxShadow: [BoxShadow(color: colors.first.withValues(alpha: 0.4), blurRadius: 16, offset: const Offset(0, 4))],
        ),
        child: child,
      );
}

/// Animated kicker that "types" then glows — AI agent feel.
class AgentKicker extends StatelessWidget {
  final String label;
  final IconData icon;
  const AgentKicker({super.key, required this.label, this.icon = Icons.auto_awesome_outlined});

  @override
  Widget build(BuildContext context) => Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            padding: const EdgeInsets.all(6),
            decoration: BoxDecoration(
              gradient: const LinearGradient(colors: [AppColors.cyan, AppColors.violet]),
              borderRadius: BorderRadius.circular(9),
            ),
            child: Icon(icon, color: AppColors.ink900, size: 15),
          ),
          const SizedBox(width: 9),
          Text(label.toUpperCase(), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 1.4, color: AppColors.cyanSoft)),
        ],
      );
}

/// Status token — linked to backend CaseStatus buckets.
enum AgentStatus { ready, needInfo, review, block, idle }

class StatusToken extends StatelessWidget {
  final AgentStatus status;
  final String label;
  const StatusToken({super.key, required this.status, required this.label});

  @override
  Widget build(BuildContext context) {
    final (fg, bg, icon) = _cfg(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(999), border: Border.all(color: fg.withValues(alpha: 0.4))),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: fg),
          const SizedBox(width: 5),
          Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w800, color: fg, letterSpacing: 0.2)),
        ],
      ),
    );
  }

  (Color, Color, IconData) _cfg(AgentStatus s) => switch (s) {
        AgentStatus.ready => (AppColors.ready, AppColors.readyBg, Icons.check_circle_outlined),
        AgentStatus.needInfo => (AppColors.needInfo, AppColors.needInfoBg, Icons.info_outline),
        AgentStatus.review => (AppColors.review, AppColors.reviewBg, Icons.gavel_outlined),
        AgentStatus.block => (AppColors.block, AppColors.blockBg, Icons.block_outlined),
        AgentStatus.idle => (AppColors.muted, AppColors.ink700, Icons.circle_outlined),
      };
}

/// Neon metric tile with animated count-in.
class NeonMetric extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color accent;
  final String? sub;
  const NeonMetric({super.key, required this.label, required this.value, required this.icon, required this.accent, this.sub});

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      glow: accent,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(label.toUpperCase(), style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800, color: AppColors.muted, letterSpacing: 0.6)),
              Container(
                padding: const EdgeInsets.all(7),
                decoration: BoxDecoration(color: accent.withValues(alpha: 0.14), borderRadius: BorderRadius.circular(10)),
                child: Icon(icon, color: accent, size: 16),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(value, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700, color: AppColors.txt, letterSpacing: -1, fontFamily: 'Space Grotesk')),
          if (sub != null) ...[const SizedBox(height: 3), Text(sub!, style: const TextStyle(fontSize: 10, color: AppColors.muted))],
        ],
      ),
    );
  }
}

/// ── Agent pipeline visualization (README §4) ──────────────────────────────
/// Intake → Confirm Gate → Router → Specialists → Risk Gate → Approval.
class AgentPipeline extends StatelessWidget {
  /// Stage indices: 0 intake,1 confirm,2 router,3 specialist,4 risk,5 approval.
  final int activeStage;
  final Set<int> doneStages;
  const AgentPipeline({super.key, required this.activeStage, this.doneStages = const {}});

  static const _stages = [
    ('Intake', Icons.upload_file_outlined),
    ('Confirm', Icons.verified_user_outlined),
    ('Route', Icons.account_tree_outlined),
    ('Agents', Icons.hub_outlined),
    ('Risk Gate', Icons.shield_outlined),
    ('Approve', Icons.gavel_outlined),
  ];

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const AgentKicker(label: 'Multi-Agent Workflow', icon: Icons.schema_outlined),
          const SizedBox(height: 16),
          LayoutBuilder(
            builder: (context, c) {
              final w = c.maxWidth;
              if (w < 640) {
                return Column(children: [for (int i = 0; i < _stages.length; i++) _stageRow(i, w)]);
              }
              return Row(children: [for (int i = 0; i < _stages.length; i++) ...[_stageNode(i), if (i < _stages.length - 1) _connector(i)]]);
            },
          ),
        ],
      ),
    );
  }

  Widget _stageNode(int i) {
    final (label, icon) = _stages[i];
    final done = doneStages.contains(i);
    final active = i == activeStage;
    final accent = active ? AppColors.cyan : done ? AppColors.lime : AppColors.subtle;
    return Expanded(
      child: Column(
        children: [
          AnimatedContainer(
            duration: const Duration(milliseconds: 350),
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: active || done ? const LinearGradient(colors: [AppColors.cyan, AppColors.violet]) : null,
              color: active || done ? null : AppColors.ink700,
              border: Border.all(color: accent.withValues(alpha: 0.7), width: 2),
              boxShadow: active ? [BoxShadow(color: AppColors.cyan.withValues(alpha: 0.5), blurRadius: 18)] : null,
            ),
            child: Center(child: Icon(icon, color: (active || done) ? AppColors.ink900 : AppColors.subtle, size: 22)),
          ),
          const SizedBox(height: 8),
          Text(label, textAlign: TextAlign.center, style: TextStyle(fontSize: 11.5, fontWeight: FontWeight.w700, color: active || done ? AppColors.txt : AppColors.muted)),
        ],
      ),
    );
  }

  Widget _connector(int i) {
    final reached = i < activeStage || doneStages.contains(i);
    return Expanded(
      child: Container(
        margin: const EdgeInsets.only(bottom: 26),
        height: 2,
        decoration: BoxDecoration(
          gradient: LinearGradient(colors: [reached ? AppColors.cyan : AppColors.line, reached ? AppColors.violet : AppColors.line]),
        ),
      ),
    );
  }

  Widget _stageRow(int i, double w) {
    final (label, icon) = _stages[i];
    final done = doneStages.contains(i);
    final active = i == activeStage;
    final accent = active ? AppColors.cyan : done ? AppColors.lime : AppColors.subtle;
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: active || done ? const LinearGradient(colors: [AppColors.cyan, AppColors.violet]) : null,
              color: active || done ? null : AppColors.ink700,
              border: Border.all(color: accent, width: 2),
            ),
            child: Center(child: Icon(icon, color: (active || done) ? AppColors.ink900 : AppColors.subtle, size: 18)),
          ),
          const SizedBox(width: 12),
          Container(
            margin: const EdgeInsets.only(bottom: 0),
            width: 26,
            height: 2,
            color: (i < activeStage || doneStages.contains(i)) ? AppColors.cyan : AppColors.line,
          ),
          const SizedBox(width: 12),
          Text(label, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: active || done ? AppColors.txt : AppColors.muted)),
        ],
      ),
    );
  }
}

/// Shimmer placeholder for loading agent panels.
class AgentShimmer extends StatelessWidget {
  final double height;
  final double? width;
  final double radius;
  const AgentShimmer({super.key, this.height = 16, this.width, this.radius = 10});

  @override
  Widget build(BuildContext context) => Shimmer.fromColors(
        baseColor: AppColors.ink700,
        highlightColor: AppColors.ink600,
        child: Container(
          width: width,
          height: height,
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(radius)),
        ),
      );
}

/// Glowing section header used across screens.
class SectionHeader extends StatelessWidget {
  final String title;
  final String? caption;
  final IconData icon;
  final Widget? trailing;
  const SectionHeader({super.key, required this.title, this.caption, this.icon = Icons.widgets_outlined, this.trailing});

  @override
  Widget build(BuildContext context) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(color: AppColors.cyan.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(11)),
            child: Icon(icon, color: AppColors.cyan, size: 18),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 17, color: AppColors.txt)),
                if (caption != null) ...[const SizedBox(height: 2), Text(caption!, style: const TextStyle(fontSize: 12, color: AppColors.muted))],
              ],
            ),
          ),
          if (trailing != null) trailing!,
        ],
      );
}
