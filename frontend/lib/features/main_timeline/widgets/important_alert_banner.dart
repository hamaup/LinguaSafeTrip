import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:frontend/features/main_timeline/providers/timeline_provider.dart';

class ImportantAlertBanner extends ConsumerWidget {
  const ImportantAlertBanner({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final alert = ref.watch(timelineProvider.select((state) => state.importantAlert));

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 300),
      child: alert != null
          ? Container(
              key: ValueKey(alert.id),
              color: Theme.of(context).colorScheme.errorContainer,
              padding: const EdgeInsets.all(12),
              child: Row(
                children: [
                  const Icon(Icons.warning_amber, size: 24),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(alert.title, style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        )),
                        Text(alert.message, maxLines: 1, overflow: TextOverflow.ellipsis),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close),
                    onPressed: () => ref.read(timelineProvider.notifier).dismissImportantAlert(),
                  ),
                ],
              ),
            )
          : const SizedBox.shrink(),
    );
  }
}
