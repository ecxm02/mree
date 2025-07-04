/// Password validation utilities to match backend requirements
class PasswordValidator {
  /// Validates password strength according to backend requirements
  /// Password must be at least 8 characters and contain:
  /// - At least one uppercase letter
  /// - At least one lowercase letter
  /// - At least one number
  static String? validatePassword(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter a password';
    }

    if (value.length < 8) {
      return 'Password must be at least 8 characters long';
    }

    if (value.length > 128) {
      return 'Password too long (max 128 characters)';
    }

    // Check for at least one uppercase letter
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return 'Password must contain at least one uppercase letter';
    }

    // Check for at least one lowercase letter
    if (!value.contains(RegExp(r'[a-z]'))) {
      return 'Password must contain at least one lowercase letter';
    }

    // Check for at least one number
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain at least one number';
    }

    return null;
  }

  /// Gets a friendly description of password requirements
  static String getPasswordRequirements() {
    return 'Password must be at least 8 characters and contain:\n'
        '• At least one uppercase letter (A-Z)\n'
        '• At least one lowercase letter (a-z)\n'
        '• At least one number (0-9)';
  }

  /// Validates username according to backend requirements
  static String? validateUsername(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter a username';
    }

    final trimmed = value.trim();

    if (trimmed.length < 3) {
      return 'Username must be at least 3 characters';
    }

    if (trimmed.length > 50) {
      return 'Username too long (max 50 characters)';
    }

    // Only allow alphanumeric, underscore, and hyphen
    if (!RegExp(r'^[a-zA-Z0-9_-]+$').hasMatch(trimmed)) {
      return 'Username can only contain letters, numbers, underscore, and hyphen';
    }

    return null;
  }
}
