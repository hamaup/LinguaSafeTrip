import 'package:flutter/material.dart';

class VoiceRecordingRipple extends StatefulWidget {
  final bool isRecording;
  final double size;

  const VoiceRecordingRipple({
    super.key,
    required this.isRecording,
    this.size = 60.0,
  });

  @override
  State<VoiceRecordingRipple> createState() => _VoiceRecordingRippleState();
}

class _VoiceRecordingRippleState extends State<VoiceRecordingRipple>
    with TickerProviderStateMixin {
  late AnimationController _controller1;
  late AnimationController _controller2;
  late AnimationController _controller3;
  late Animation<double> _animation1;
  late Animation<double> _animation2;
  late Animation<double> _animation3;

  @override
  void initState() {
    super.initState();

    _controller1 = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _controller2 = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _controller3 = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );

    _animation1 = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller1,
      curve: Curves.easeOut,
    ));

    _animation2 = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller2,
      curve: Curves.easeOut,
    ));

    _animation3 = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _controller3,
      curve: Curves.easeOut,
    ));

    if (widget.isRecording) {
      _startAnimations();
    }
  }

  void _startAnimations() {
    _controller1.repeat();
    Future.delayed(const Duration(milliseconds: 600), () {
      if (mounted) _controller2.repeat();
    });
    Future.delayed(const Duration(milliseconds: 1200), () {
      if (mounted) _controller3.repeat();
    });
  }

  void _stopAnimations() {
    _controller1.stop();
    _controller2.stop();
    _controller3.stop();
    _controller1.reset();
    _controller2.reset();
    _controller3.reset();
  }

  @override
  void didUpdateWidget(VoiceRecordingRipple oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isRecording != oldWidget.isRecording) {
      if (widget.isRecording) {
        _startAnimations();
      } else {
        _stopAnimations();
      }
    }
  }

  @override
  void dispose() {
    _controller1.dispose();
    _controller2.dispose();
    _controller3.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.isRecording) {
      return const SizedBox.shrink();
    }

    return SizedBox(
      width: widget.size,
      height: widget.size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          _buildRipple(_animation1),
          _buildRipple(_animation2),
          _buildRipple(_animation3),
        ],
      ),
    );
  }

  Widget _buildRipple(Animation<double> animation) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) {
        return Container(
          width: widget.size * animation.value,
          height: widget.size * animation.value,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            border: Border.all(
              color: Colors.red.withValues(alpha: 0.5 * (1 - animation.value)),
              width: 3.0 * (1 - animation.value * 0.5),
            ),
          ),
        );
      },
    );
  }
}