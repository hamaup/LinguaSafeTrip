// Temporary model for P1-008 implementation
// Will be replaced by actual implementation in P1-010

class EmergencyContactModel {
  final String id;
  final String name;
  final String phoneNumber;
  final String? relationship;

  EmergencyContactModel({
    required this.id,
    required this.name,
    required this.phoneNumber,
    this.relationship,
  });

  EmergencyContactModel copyWith({
    String? id,
    String? name,
    String? phoneNumber,
    String? relationship,
  }) {
    return EmergencyContactModel(
      id: id ?? this.id,
      name: name ?? this.name,
      phoneNumber: phoneNumber ?? this.phoneNumber,
      relationship: relationship ?? this.relationship,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'phoneNumber': phoneNumber,
    if (relationship != null) 'relationship': relationship,
  };

  factory EmergencyContactModel.fromJson(Map<String, dynamic> json) {
    return EmergencyContactModel(
      id: json['id'] as String,
      name: json['name'] as String,
      phoneNumber: json['phoneNumber'] as String,
      relationship: json['relationship'] as String?,
    );
  }
}
