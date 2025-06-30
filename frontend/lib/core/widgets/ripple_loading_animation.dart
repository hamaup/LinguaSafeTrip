import 'package:flutter/material.dart';
import 'dart:math' as math;

class RippleLoadingAnimation extends StatefulWidget {
  final double size;
  final Color color;
  final Widget? child;

  const RippleLoadingAnimation({
    super.key,
    this.size = 200,
    this.color = Colors.black,
    this.child,
  });

  @override
  State<RippleLoadingAnimation> createState() => _RippleLoadingAnimationState();
}

class _RippleLoadingAnimationState extends State<RippleLoadingAnimation>
    with TickerProviderStateMixin {
  late List<AnimationController> _controllers;
  late List<Animation<double>> _animations;
  
  static const int rippleCount = 3;

  @override
  void initState() {
    super.initState();
    
    _controllers = List.generate(
      rippleCount,
      (index) => AnimationController(
        vsync: this,
        duration: Duration(milliseconds: 8000 + (index * 1600)),
      ),
    );
    
    _animations = _controllers.map((controller) {
      return Tween<double>(
        begin: 0.0,
        end: 1.0,
      ).animate(
        CurvedAnimation(
          parent: controller,
          curve: Curves.easeOut,
        ),
      );
    }).toList();
    
    // Start animations with delays
    for (int i = 0; i < _controllers.length; i++) {
      Future.delayed(Duration(milliseconds: i * 1600), () {
        if (mounted) {
          _controllers[i].repeat();
        }
      });
    }
  }

  @override
  void dispose() {
    for (var controller in _controllers) {
      controller.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          // Ripple animations
          ...List.generate(rippleCount, (index) {
            return AnimatedBuilder(
              animation: _animations[index],
              builder: (context, child) {
                return Container(
                  width: widget.size * _animations[index].value,
                  height: widget.size * _animations[index].value,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    border: Border.all(
                      color: widget.color.withValues(
                        alpha: math.max(0, 1 - _animations[index].value) * 0.15,
                      ),
                      width: 2 * (1 - _animations[index].value * 0.5),
                    ),
                  ),
                );
              },
            );
          }),
          // Center content
          if (widget.child != null) widget.child!,
        ],
      ),
    );
  }
}