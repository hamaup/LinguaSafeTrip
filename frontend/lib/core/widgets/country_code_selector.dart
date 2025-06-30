import 'package:flutter/material.dart';
import '../constants/country_codes.dart';

class CountryCodeSelector extends StatelessWidget {
  final CountryCode selectedCountry;
  final Function(CountryCode) onCountrySelected;

  const CountryCodeSelector({
    super.key,
    required this.selectedCountry,
    required this.onCountrySelected,
  });

  void _showCountryPicker(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => _CountryPickerSheet(
        selectedCountry: selectedCountry,
        onCountrySelected: onCountrySelected,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () => _showCountryPicker(context),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFFF0FFFE).withValues(alpha: 0.5),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: const Color(0xFFB2F5EA).withValues(alpha: 0.5),
            width: 0.5,
          ),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              selectedCountry.flag,
              style: const TextStyle(fontSize: 20),
            ),
            const SizedBox(width: 8),
            Text(
              selectedCountry.dialCode,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w500,
                color: Color(0xFF2D4A4A),
              ),
            ),
            const SizedBox(width: 4),
            const Icon(
              Icons.arrow_drop_down,
              size: 20,
              color: Color(0xFF5FA8A8),
            ),
          ],
        ),
      ),
    );
  }
}

class _CountryPickerSheet extends StatefulWidget {
  final CountryCode selectedCountry;
  final Function(CountryCode) onCountrySelected;

  const _CountryPickerSheet({
    required this.selectedCountry,
    required this.onCountrySelected,
  });

  @override
  State<_CountryPickerSheet> createState() => _CountryPickerSheetState();
}

class _CountryPickerSheetState extends State<_CountryPickerSheet> {
  late List<CountryCode> filteredCountries;
  final TextEditingController searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    filteredCountries = countryCodes;
  }

  void _filterCountries(String query) {
    setState(() {
      if (query.isEmpty) {
        filteredCountries = countryCodes;
      } else {
        filteredCountries = countryCodes.where((country) {
          return country.name.toLowerCase().contains(query.toLowerCase()) ||
                 country.dialCode.contains(query) ||
                 country.code.toLowerCase().contains(query.toLowerCase());
        }).toList();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: MediaQuery.of(context).size.height * 0.7,
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      child: Column(
        children: [
          // ハンドル
          Container(
            margin: const EdgeInsets.only(top: 12),
            width: 40,
            height: 4,
            decoration: BoxDecoration(
              color: const Color(0xFFE8FFFC),
              borderRadius: BorderRadius.circular(2),
            ),
          ),
          // タイトル
          Padding(
            padding: const EdgeInsets.all(20),
            child: Text(
              '国番号を選択',
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: const Color(0xFF2D4A4A),
              ),
            ),
          ),
          // 検索フィールド
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Container(
              decoration: BoxDecoration(
                color: const Color(0xFFF0FFFE),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFFB2F5EA).withValues(alpha: 0.5),
                  width: 0.5,
                ),
              ),
              child: TextField(
                controller: searchController,
                onChanged: _filterCountries,
                decoration: InputDecoration(
                  hintText: '国名または国番号で検索...',
                  hintStyle: TextStyle(color: const Color(0xFF9ECECE)),
                  prefixIcon: Icon(
                    Icons.search_rounded,
                    color: const Color(0xFF00D9FF),
                  ),
                  border: InputBorder.none,
                  contentPadding: const EdgeInsets.all(16),
                ),
              ),
            ),
          ),
          const SizedBox(height: 16),
          // 国リスト
          Expanded(
            child: ListView.builder(
              itemCount: filteredCountries.length,
              itemBuilder: (context, index) {
                final country = filteredCountries[index];
                final isSelected = country.code == widget.selectedCountry.code;
                
                return ListTile(
                  onTap: () {
                    widget.onCountrySelected(country);
                    Navigator.pop(context);
                  },
                  contentPadding: const EdgeInsets.symmetric(
                    horizontal: 20,
                    vertical: 8,
                  ),
                  leading: Text(
                    country.flag,
                    style: const TextStyle(fontSize: 24),
                  ),
                  title: Text(
                    country.name,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                      color: isSelected 
                          ? const Color(0xFF00D9FF)
                          : const Color(0xFF2D4A4A),
                    ),
                  ),
                  trailing: Text(
                    country.dialCode,
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w500,
                      color: isSelected 
                          ? const Color(0xFF00D9FF)
                          : const Color(0xFF5FA8A8),
                    ),
                  ),
                  selected: isSelected,
                  selectedTileColor: const Color(0xFFE8FFFC).withValues(alpha: 0.3),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    searchController.dispose();
    super.dispose();
  }
}