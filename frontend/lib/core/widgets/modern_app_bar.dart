import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:ui';

class ModernAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String title;
  final String? subtitle;
  final List<Widget>? actions;
  final Widget? leading;
  final VoidCallback? onLeadingPressed;
  final Color? backgroundColor;
  final bool showLogo;

  const ModernAppBar({
    super.key,
    required this.title,
    this.subtitle,
    this.actions,
    this.leading,
    this.onLeadingPressed,
    this.backgroundColor,
    this.showLogo = false,
  });

  @override
  Widget build(BuildContext context) {
    final baseColor = backgroundColor ?? Colors.white;
    
    return PreferredSize(
      preferredSize: const Size.fromHeight(80),
      child: ClipRRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
          child: Container(
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.85),
              border: Border(
                bottom: BorderSide(
                  color: const Color(0xFFE8FFFC).withValues(alpha: 0.3),
                  width: 0.5,
                ),
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF00E5CC).withValues(alpha: 0.03),
                  blurRadius: 20,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    // Leading icon/button
                    if (leading != null) ...[
                      Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: () {
                            HapticFeedback.lightImpact();
                            if (onLeadingPressed != null) {
                              onLeadingPressed!();
                            } else {
                              Navigator.of(context).pop();
                            }
                          },
                          borderRadius: BorderRadius.circular(20),
                          child: Container(
                            padding: const EdgeInsets.all(8),
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(20),
                              gradient: LinearGradient(
                                colors: [
                                  const Color(0xFF00D9FF).withValues(alpha: 0.15),
                                  const Color(0xFF00E5CC).withValues(alpha: 0.15),
                                ],
                              ),
                              border: Border.all(
                                color: const Color(0xFF00E5CC).withValues(alpha: 0.5),
                                width: 1,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: const Color(0xFF00D9FF).withValues(alpha: 0.2),
                                  blurRadius: 10,
                                  offset: const Offset(0, 2),
                                ),
                              ],
                            ),
                            child: leading!,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                    ],
                    
                    // Logo (optional)
                    if (showLogo) ...[
                      Container(
                        width: 40,
                        height: 40,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          gradient: LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [
                              const Color(0xFF00D9FF),  // Fresh cyan
                              const Color(0xFF00E5CC),  // Mint green
                            ],
                          ),
                          boxShadow: [
                            BoxShadow(
                              color: const Color(0xFF00E5CC).withValues(alpha: 0.25),
                              blurRadius: 8,
                              offset: const Offset(0, 2),
                            ),
                          ],
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.asset(
                            'assets/icon/app_icon.png',
                            width: 24,
                            height: 24,
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                    ],
                    
                    // Title and subtitle
                    Expanded(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            title,
                            style: const TextStyle(
                              fontSize: 24,
                              fontWeight: FontWeight.w700,
                              letterSpacing: -0.5,
                              color: Color(0xFF2D4A4A),  // Fresh dark teal
                            ),
                            overflow: TextOverflow.ellipsis,
                            maxLines: 1,
                          ),
                          if (subtitle != null)
                            Text(
                              subtitle!,
                              style: TextStyle(
                                fontSize: 13,
                                color: const Color(0xFF5FA8A8),  // Soft teal
                                letterSpacing: 0,
                              ),
                              overflow: TextOverflow.ellipsis,
                              maxLines: 1,
                            ),
                        ],
                      ),
                    ),
                    
                    // Actions
                    if (actions != null && actions!.isNotEmpty) ...[
                      const SizedBox(width: 8),
                      ...actions!.map((action) => Padding(
                        padding: const EdgeInsets.only(left: 8),
                        child: action,
                      )),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(80);
}

// Unified style for action buttons
class ModernAppBarAction extends StatelessWidget {
  final IconData icon;
  final VoidCallback onPressed;
  final bool showNotificationDot;

  const ModernAppBarAction({
    super.key,
    required this.icon,
    required this.onPressed,
    this.showNotificationDot = false,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () {
          HapticFeedback.lightImpact();
          onPressed();
        },
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            color: Colors.white.withValues(alpha: 0.98),
            border: Border.all(
              color: const Color(0xFFB2F5EA).withValues(alpha: 0.2),
              width: 0.5,
            ),
          ),
          child: Stack(
            children: [
              Icon(
                icon,
                color: const Color(0xFF5FA8A8),  // Fresh teal
                size: 22,
              ),
              if (showNotificationDot)
                Positioned(
                  right: 0,
                  top: 0,
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: const Color(0xFFEF4444),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFFEF4444).withValues(alpha: 0.4),
                          blurRadius: 6,
                          spreadRadius: 0,
                        ),
                      ],
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}