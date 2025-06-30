import 'package:flutter/foundation.dart';

/// Simple logger utility for the application
class Logger {
  final String name;
  
  Logger(this.name);
  
  void d(String message, [dynamic error, StackTrace? stackTrace]) {
    if (kDebugMode) {
      // debugPrint('[$name] DEBUG: $message');
      if (error != null) {
      // debugPrint('[$name] ERROR: $error');
        if (stackTrace != null) {
      // debugPrint('[$name] STACK: $stackTrace');
        }
      }
    }
  }
  
  void i(String message) {
      // debugPrint('[$name] INFO: $message');
  }
  
  void w(String message) {
      // debugPrint('[$name] WARN: $message');
  }
  
  void e(String message, [dynamic error, StackTrace? stackTrace]) {
      // debugPrint('[$name] ERROR: $message');
    if (error != null) {
      // debugPrint('[$name] ERROR DETAILS: $error');
    }
    if (stackTrace != null && kDebugMode) {
      // debugPrint('[$name] STACK TRACE: $stackTrace');
    }
  }
}

// Global logger instance
final logger = Logger('SafetyBee');