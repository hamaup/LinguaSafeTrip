import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:frontend/core/navigation/app_router.dart';
import 'package:frontend/core/widgets/modern_app_bar.dart';

class AppHeaderWidget extends StatelessWidget implements PreferredSizeWidget {
  const AppHeaderWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return ModernAppBar(
      title: 'LinguaSafeTrip',
      showLogo: true,
      actions: [
        ModernAppBarAction(
          icon: Icons.settings_outlined,
          onPressed: () => context.goNamed(AppRoutes.settings),
          showNotificationDot: true,
        ),
      ],
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(80);
}
