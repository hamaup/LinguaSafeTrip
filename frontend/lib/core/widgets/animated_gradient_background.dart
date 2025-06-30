import 'package:flutter/material.dart';
import 'dart:math' as math;

class AnimatedGradientBackground extends StatefulWidget {
  final Widget child;
  final bool isEmergencyMode;

  const AnimatedGradientBackground({
    super.key,
    required this.child,
    this.isEmergencyMode = false,
  });

  @override
  State<AnimatedGradientBackground> createState() => _AnimatedGradientBackgroundState();
}

class _AnimatedGradientBackgroundState extends State<AnimatedGradientBackground>
    with TickerProviderStateMixin {
  late AnimationController _rippleController;
  late AnimationController _rippleController2;
  late AnimationController _rippleController3;
  late Animation<double> _rippleAnimation;
  late Animation<double> _rippleAnimation2;
  late Animation<double> _rippleAnimation3;

  @override
  void initState() {
    super.initState();
    
    // 3つの波紋アニメーション（異なるタイミングで開始）
    _rippleController = AnimationController(
      duration: const Duration(seconds: 4),
      vsync: this,
    )..repeat();

    _rippleController2 = AnimationController(
      duration: const Duration(seconds: 4),
      vsync: this,
    )..repeat(reverse: false);

    _rippleController3 = AnimationController(
      duration: const Duration(seconds: 4),
      vsync: this,
    )..repeat(reverse: false);

    _rippleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _rippleController,
      curve: Curves.easeOut,
    ));

    _rippleAnimation2 = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _rippleController2,
      curve: Curves.easeOut,
    ));

    _rippleAnimation3 = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _rippleController3,
      curve: Curves.easeOut,
    ));

    // 波紋を順番に開始
    Future.delayed(const Duration(milliseconds: 1333), () {
      if (mounted) {
        _rippleController2.repeat();
      }
    });
    Future.delayed(const Duration(milliseconds: 2666), () {
      if (mounted) {
        _rippleController3.repeat();
      }
    });
  }

  @override
  void dispose() {
    _rippleController.dispose();
    _rippleController2.dispose();
    _rippleController3.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // クリーンなグラデーション背景
        Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: widget.isEmergencyMode
                  ? [
                      const Color(0xFFFFF9F9),
                      const Color(0xFFFFE5E5),
                      const Color(0xFFFFEFEF),
                    ]
                  : [
                      const Color(0xFFF0FFFE),  // Mint water
                      const Color(0xFFE8FFFC),  // Aqua mist
                      const Color(0xFFF5FFFD),  // Fresh dew
                    ],
            ),
          ),
        ),
        // ソフトな波紋エフェクト1
        AnimatedBuilder(
          animation: _rippleAnimation,
          builder: (context, child) {
            return CustomPaint(
              painter: CenterRipplePainter(
                animationValue: _rippleAnimation.value,
                color: widget.isEmergencyMode
                    ? const Color(0xFFFF6B6B).withValues(alpha: 0.08)
                    : const Color(0xFF00E5CC).withValues(alpha: 0.06),  // Fresh mint
                strokeWidth: 0.5,
              ),
              size: Size.infinite,
            );
          },
        ),
        // ソフトな波紋エフェクト2
        AnimatedBuilder(
          animation: _rippleAnimation2,
          builder: (context, child) {
            return CustomPaint(
              painter: CenterRipplePainter(
                animationValue: _rippleAnimation2.value,
                color: widget.isEmergencyMode
                    ? const Color(0xFFFF8787).withValues(alpha: 0.06)
                    : const Color(0xFF7FDBFF).withValues(alpha: 0.05),  // Sky water
                strokeWidth: 0.3,
              ),
              size: Size.infinite,
            );
          },
        ),
        // ソフトな波紋エフェクト3
        AnimatedBuilder(
          animation: _rippleAnimation3,
          builder: (context, child) {
            return CustomPaint(
              painter: CenterRipplePainter(
                animationValue: _rippleAnimation3.value,
                color: widget.isEmergencyMode
                    ? const Color(0xFFFFA8A8).withValues(alpha: 0.05)
                    : const Color(0xFFB2F5EA).withValues(alpha: 0.04),  // Fresh green
                strokeWidth: 0.2,
              ),
              size: Size.infinite,
            );
          },
        ),
        // 微細なグラデーションオーバーレイ
        Container(
          decoration: BoxDecoration(
            gradient: RadialGradient(
              center: Alignment.center,
              radius: 1.2,
              colors: [
                Colors.white.withValues(alpha: 0.15),
                Colors.transparent,
                const Color(0xFFE8FFFC).withValues(alpha: 0.10),
              ],
              stops: const [0.0, 0.6, 1.0],
            ),
          ),
        ),
        // コンテンツ
        widget.child,
      ],
    );
  }
}

// 中心から広がる波紋エフェクト用のペインター
class CenterRipplePainter extends CustomPainter {
  final double animationValue;
  final Color color;
  final double strokeWidth;

  CenterRipplePainter({
    required this.animationValue,
    required this.color,
    this.strokeWidth = 0.5,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final maxRadius = math.sqrt(
      math.pow(size.width / 2, 2) + math.pow(size.height / 2, 2)
    );
    
    // 波紋の描画
    final rippleRadius = maxRadius * animationValue;
    final colorAlpha = ((color.a * 255.0).round() & 0xff) / 255.0;
    final opacity = (1 - animationValue) * colorAlpha;
    
    final paint = Paint()
      ..color = color.withValues(alpha: opacity)
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth;
    
    canvas.drawCircle(center, rippleRadius, paint);
    
    // グラデーション効果
    final gradientPaint = Paint()
      ..shader = RadialGradient(
        center: Alignment.center,
        radius: 1.0,
        colors: [
          color.withValues(alpha: opacity * 0.5),
          color.withValues(alpha: opacity * 0.1),
          Colors.transparent,
        ],
        stops: const [0.0, 0.7, 1.0],
      ).createShader(Rect.fromCircle(center: center, radius: rippleRadius));
    
    canvas.drawCircle(center, rippleRadius * 0.98, gradientPaint);
  }

  @override
  bool shouldRepaint(CenterRipplePainter oldDelegate) {
    return animationValue != oldDelegate.animationValue ||
           color != oldDelegate.color ||
           strokeWidth != oldDelegate.strokeWidth;
  }
}