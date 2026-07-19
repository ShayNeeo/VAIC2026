import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/controllers/employee_workspace_controller.dart';
import '../../core/controllers/sales_case_controller.dart';
import '../../core/models/employee_models.dart';
import '../../design/design.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';

class EmployeeWorkspaceScreen extends StatefulWidget {
  const EmployeeWorkspaceScreen({super.key});

  @override
  State<EmployeeWorkspaceScreen> createState() => _EmployeeWorkspaceScreenState();
}

class _EmployeeWorkspaceScreenState extends State<EmployeeWorkspaceScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final SalesCaseController _salesCaseController = SalesCaseController();

  // Page 2 State variables
  String? _selectedCaseId;
  final List<String> _localFiles = [];
  final Map<String, bool> _selectedDocTypes = {
    'Giấy phép ĐKKD': true,
    'Báo cáo tài chính 3 năm gần nhất': true,
    'Tờ trình đề xuất cấp tín dụng': false,
    'Quyết định bổ nhiệm người đại diện': false,
  };
  bool _isUploadingDocs = false;

  // Chatbot State variables
  final TextEditingController _chatInput = TextEditingController();
  final List<ChatMessage> _chatHistory = [
    ChatMessage(
      sender: 'ai',
      text: 'Xin chào RM! Tôi là AI Copilot của bạn. Tôi có thể giúp gì cho bạn trong việc phân tích hồ sơ doanh nghiệp hôm nay?',
      thinkingSteps: [
        'Khởi tạo trợ lý AI...',
        'Truy cập dữ liệu phân khúc khách hàng doanh nghiệp...',
        'Hệ thống sẵn sàng tư vấn hồ sơ và chính sách tín dụng.',
      ],
    ),
  ];
  bool _aiThinking = false;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<EmployeeWorkspaceController>().refresh();
      _salesCaseController.loadCases();
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
    _chatInput.dispose();
    _salesCaseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider.value(value: _salesCaseController),
      ],
      child: Consumer<EmployeeWorkspaceController>(
        builder: (context, controller, _) => Scaffold(
          backgroundColor: AppColors.background,
          appBar: AppBar(
            backgroundColor: AppColors.orange,
            foregroundColor: Colors.white,
            elevation: 2,
            shadowColor: AppColors.orangeDark.withValues(alpha: 0.3),
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'RM WORKSPACE',
                  style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 0.5),
                ),
                Text(
                  controller.context?.employeeId ?? 'RM-999',
                  style: const TextStyle(fontSize: 11, color: Colors.white70),
                ),
              ],
            ),
            bottom: TabBar(
              controller: _tabController,
              indicatorColor: Colors.white,
              indicatorWeight: 3,
              labelColor: Colors.white,
              unselectedLabelColor: Colors.white70,
              labelStyle: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w800, fontSize: 13),
              tabs: const [
                Tab(icon: Icon(Icons.folder_shared_outlined), text: 'YÊU CẦU TỪ KHÁCH HÀNG'),
                Tab(icon: Icon(Icons.cloud_upload_outlined), text: 'NHẬP LIỆU & COPILOT'),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Làm mới dữ liệu',
                onPressed: () {
                  controller.refresh();
                  _salesCaseController.loadCases();
                },
              ),
              IconButton(
                icon: const Icon(Icons.logout),
                tooltip: 'Đăng xuất',
                onPressed: () {
                  controller.logout();
                  context.go('/login');
                },
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: controller.isLoading
              ? const Center(child: CircularProgressIndicator(color: AppColors.orange))
              : TabBarView(
                  controller: _tabController,
                  children: [
                    _buildPage1(context),
                    _buildPage2(context),
                  ],
                ),
        ),
      ),
    );
  }

  // ── PAGE 1: Yêu cầu từ doanh nghiệp (Phân chia thành 3 phần trạng thái) ──────────
  Widget _buildPage1(BuildContext context) {
    return ListenableBuilder(
      listenable: _salesCaseController,
      builder: (context, _) {
        if (_salesCaseController.isLoading) {
          return const Center(child: CircularProgressIndicator(color: AppColors.orange));
        }

        final cases = _salesCaseController.cases;

        // Phân loại hồ sơ theo 3 phần yêu cầu:
        // 1. Đã xử lý xong (analysis_completed, profile_confirmed, approval_issued)
        // 2. Chưa xử lý, đang chờ xử lý (draft, files_uploaded)
        // 3. Đang chờ hoàn thiện (thiếu tài liệu - extraction_completed hoặc processing_failed)
        final List<Map<String, dynamic>> doneCases = [];
        final List<Map<String, dynamic>> pendingCases = [];
        final List<Map<String, dynamic>> incompleteCases = [];

        for (final c in cases) {
          final status = (c['intake_status'] ?? 'draft').toString();
          if (status == 'analysis_completed' || status == 'profile_confirmed' || status == 'approval_issued') {
            doneCases.add(c);
          } else if (status == 'draft' || status == 'files_uploaded') {
            pendingCases.add(c);
          } else {
            incompleteCases.add(c);
          }
        }

        return LayoutBuilder(
          builder: (context, constraints) {
            final isWide = constraints.maxWidth > 900;
            if (isWide) {
              // Giao diện Kanban 3 cột song song cực chuyên nghiệp
              return Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(child: _buildKanbanColumn('ĐÃ XỬ LÝ XONG', doneCases, Colors.green, Icons.check_circle_outline)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildKanbanColumn('CHƯA / CHỜ XỬ LÝ', pendingCases, AppColors.orange, Icons.hourglass_empty)),
                    const SizedBox(width: 12),
                    Expanded(child: _buildKanbanColumn('ĐANG CHỜ HOÀN THIỆN', incompleteCases, Colors.red, Icons.warning_amber_outlined)),
                  ],
                ),
              );
            } else {
              // Màn hình dọc, dùng danh sách xếp chồng ExpansionTile
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildExpansionSection('ĐÃ XỬ LÝ XONG (${doneCases.length})', doneCases, Colors.green, Icons.check_circle_outline),
                  const SizedBox(height: 12),
                  _buildExpansionSection('CHƯA / CHỜ XỬ LÝ (${pendingCases.length})', pendingCases, AppColors.orange, Icons.hourglass_empty),
                  const SizedBox(height: 12),
                  _buildExpansionSection('ĐANG CHỜ HOÀN THIỆN (${incompleteCases.length})', incompleteCases, Colors.red, Icons.warning_amber_outlined),
                ],
              );
            }
          },
        );
      },
    );
  }

  Widget _buildKanbanColumn(String title, List<Map<String, dynamic>> items, Color themeColor, IconData icon) {
    return Card(
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: themeColor.withValues(alpha: 0.3), width: 1.5),
      ),
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: themeColor, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 13, color: themeColor),
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                  decoration: BoxDecoration(color: themeColor.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(10)),
                  child: Text(
                    '${items.length}',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: themeColor),
                  ),
                ),
              ],
            ),
            const Divider(height: 24, thickness: 1.5),
            Expanded(
              child: items.isEmpty
                  ? Center(
                      child: Text(
                        'Không có hồ sơ nào',
                        style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontStyle: FontStyle.italic),
                      ),
                    )
                  : ListView.builder(
                      itemCount: items.length,
                      itemBuilder: (context, index) {
                        final item = items[index];
                        return _buildCaseItemCard(item);
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExpansionSection(String title, List<Map<String, dynamic>> items, Color themeColor, IconData icon) {
    return Card(
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: themeColor.withValues(alpha: 0.2)),
      ),
      elevation: 2,
      child: ExpansionTile(
        initiallyExpanded: true,
        leading: Icon(icon, color: themeColor),
        title: Text(
          title,
          style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w800, fontSize: 14, color: AppColors.textPrimary),
        ),
        childrenPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        children: items.isEmpty
            ? [
                const Padding(
                  padding: EdgeInsets.all(16),
                  child: Text('Không có hồ sơ nào.', style: TextStyle(fontSize: 12, color: AppColors.textSecondary)),
                )
              ]
            : items.map((item) => _buildCaseItemCard(item)).toList(),
      ),
    );
  }

  Widget _buildCaseItemCard(Map<String, dynamic> c) {
    final caseId = (c['case_id'] ?? '').toString();
    final companyName = (c['company_name'] ?? c['customer_id'] ?? 'Doanh nghiệp').toString();
    final status = (c['intake_status'] ?? 'draft').toString();
    final priority = (c['priority'] ?? 'normal').toString();

    return Card(
      color: AppColors.orangeBackground,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.border),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        title: Text(
          companyName,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13.5, color: AppColors.textPrimary),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text('ID: $caseId', style: GoogleFonts.jetBrainsMono(fontSize: 10.5, color: AppColors.textSecondary)),
            const SizedBox(height: 4),
            Row(
              children: [
                _buildSmallBadge(status.toUpperCase(), AppColors.orange),
                const SizedBox(width: 6),
                _buildSmallBadge(priority.toUpperCase(), priority == 'high' ? Colors.red : Colors.blue),
              ],
            ),
          ],
        ),
        trailing: const Icon(Icons.arrow_forward_ios, size: 14, color: AppColors.orange),
        onTap: () {
          // Khi nhấn vào hồ sơ, chuyển sang Page 2 và chọn doanh nghiệp đó
          setState(() {
            _selectedCaseId = caseId;
          });
          _tabController.animateTo(1);
        },
      ),
    );
  }

  Widget _buildSmallBadge(String text, Color color) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(6)),
      child: Text(
        text,
        style: TextStyle(color: color, fontSize: 9.5, fontWeight: FontWeight.bold),
      ),
    );
  }

  // ── PAGE 2: Nhập liệu thông tin & Chatbot AI (Tỷ lệ 3/7) ──────────
  Widget _buildPage2(BuildContext context) {
    return Row(
      children: [
        // ── 3/10 BÊN TRÁI: NHẬP LIỆU THÔNG TIN ──
        Expanded(
          flex: 3,
          child: Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(right: BorderSide(color: AppColors.border, width: 1.5)),
            ),
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'NHẬP LIỆU HỒ SƠ',
                    style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 14, color: AppColors.orangeDark),
                  ),
                  const SizedBox(height: 16),

                  // ── 1. Upload tài liệu trực tiếp từ máy tính ──
                  _buildSubSectionHeader('1. TẢI TÀI LIỆU LÊN', Icons.computer_outlined),
                  const SizedBox(height: 8),
                  InkWell(
                    onTap: _pickLocalFile,
                    child: Container(
                      height: 85,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppColors.orangeBackground,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: AppColors.orange.withValues(alpha: 0.5), width: 1.5),
                      ),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.file_open_outlined, color: AppColors.orange, size: 24),
                          const SizedBox(height: 6),
                          Text(
                            'Chọn tệp từ máy tính của bạn...',
                            style: GoogleFonts.beVietnamPro(fontSize: 11, color: AppColors.orangeDark, fontWeight: FontWeight.w600),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                  if (_localFiles.isNotEmpty)
                    Wrap(
                      spacing: 6,
                      runSpacing: 6,
                      children: _localFiles.map((f) => Chip(
                        label: Text(f, style: const TextStyle(fontSize: 10)),
                        deleteIcon: const Icon(Icons.close, size: 12),
                        onDeleted: () => setState(() => _localFiles.remove(f)),
                        backgroundColor: AppColors.orangeLight,
                      )).toList(),
                    ),

                  const Divider(height: 32, thickness: 1.2),

                  // ── 2. Chọn doanh nghiệp -> chọn tài liệu cần upload (có thể bỏ chọn) ──
                  _buildSubSectionHeader('2. DOANH NGHIỆP & TÀI LIỆU', Icons.business_outlined),
                  const SizedBox(height: 10),
                  ListenableBuilder(
                    listenable: _salesCaseController,
                    builder: (context, _) {
                      final cases = _salesCaseController.cases;
                      return DropdownButtonFormField<String>(
                        value: _selectedCaseId != null && cases.any((c) => c['case_id'] == _selectedCaseId) ? _selectedCaseId : null,
                        hint: const Text('Chọn khách hàng doanh nghiệp', style: TextStyle(fontSize: 12)),
                        style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'BeVietnamPro'),
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.corporate_fare_outlined, color: AppColors.orange),
                          contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                        ),
                        items: cases.map((c) {
                          final caseId = (c['case_id'] ?? '').toString();
                          final comp = (c['company_name'] ?? caseId).toString();
                          return DropdownMenuItem<String>(
                            value: caseId,
                            child: Text('$comp ($caseId)'),
                          );
                        }).toList(),
                        onChanged: (val) {
                          setState(() {
                            _selectedCaseId = val;
                          });
                        },
                      );
                    },
                  ),
                  const SizedBox(height: 12),
                  if (_selectedCaseId != null) ...[
                    const Text(
                      'Tài liệu yêu cầu (Có thể bỏ chọn):',
                      style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 4),
                    Column(
                      children: _selectedDocTypes.keys.map((type) {
                        return CheckboxListTile(
                          title: Text(type, style: const TextStyle(fontSize: 11)),
                          value: _selectedDocTypes[type],
                          activeColor: AppColors.orange,
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          onChanged: (val) {
                            setState(() {
                              _selectedDocTypes[type] = val ?? false;
                            });
                          },
                        );
                      }).toList(),
                    ),
                  ],

                  const Divider(height: 32, thickness: 1.2),

                  // ── 3. Danh sách các tài liệu đang được chọn & Nút tải lên ──
                  _buildSubSectionHeader('3. TÀI LIỆU ĐANG CHỌN', Icons.list_alt_outlined),
                  const SizedBox(height: 10),
                  _buildSelectedFilesList(),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _isUploadingDocs || _selectedCaseId == null || (_localFiles.isEmpty && !_selectedDocTypes.containsValue(true))
                          ? null
                          : _handleUploadDocuments,
                      icon: const Icon(Icons.cloud_upload),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.orange,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      label: Text(_isUploadingDocs ? 'Đang tải lên...' : 'Tải lên hệ thống'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),

        // ── 7/10 BÊN PHẢI: BOTCHAT CHATBOT AI ──
        Expanded(
          flex: 7,
          child: Container(
            color: AppColors.orangeBackground,
            child: Column(
              children: [
                // Header Chatbot
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    border: Border(bottom: BorderSide(color: AppColors.border)),
                  ),
                  child: Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(color: AppColors.orange.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(10)),
                        child: const Icon(Icons.psychology_outlined, color: AppColors.orange, size: 22),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'AI SALES COPILOT',
                              style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 14, color: AppColors.orangeDark),
                            ),
                            const Text('Hỗ trợ tư vấn, thẩm định và phản hồi hồ sơ tín dụng', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                // Tin nhắn đối thoại
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _chatHistory.length + (_aiThinking ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index == _chatHistory.length && _aiThinking) {
                        return _buildThinkingBubble();
                      }
                      return _buildChatBubble(_chatHistory[index]);
                    },
                  ),
                ),

                // Ô nhập liệu chat
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    border: Border(top: BorderSide(color: AppColors.border)),
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _chatInput,
                          style: const TextStyle(fontSize: 13),
                          decoration: InputDecoration(
                            hintText: 'Đặt câu hỏi phân tích cho AI Copilot...',
                            fillColor: AppColors.orangeBackground,
                            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                            border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
                            enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
                            focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: const BorderSide(color: AppColors.orange, width: 1.5)),
                          ),
                          onSubmitted: (_) => _handleSendChatMessage(),
                        ),
                      ),
                      const SizedBox(width: 8),
                      IconButton(
                        icon: const Icon(Icons.send),
                        color: AppColors.orange,
                        onPressed: _handleSendChatMessage,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildSubSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: AppColors.textSecondary, size: 16),
        const SizedBox(width: 6),
        Text(
          title,
          style: GoogleFonts.beVietnamPro(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary, letterSpacing: 0.5),
        ),
      ],
    );
  }

  Widget _buildSelectedFilesList() {
    final List<String> items = [];
    items.addAll(_localFiles);
    _selectedDocTypes.forEach((key, value) {
      if (value && _selectedCaseId != null) {
        items.add('$key (Theo khách hàng)');
      }
    });

    if (items.isEmpty) {
      return Container(
        padding: const EdgeInsets.all(12),
        width: double.infinity,
        decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: AppColors.border)),
        child: const Text('Chưa chọn tài liệu nào để tải lên.', style: TextStyle(fontSize: 11, color: AppColors.textDisabled, fontStyle: FontStyle.italic)),
      );
    }

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFFFFFDFB),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        children: items.map((f) => ListTile(
          dense: true,
          visualDensity: VisualDensity.compact,
          leading: const Icon(Icons.insert_drive_file_outlined, size: 16, color: AppColors.orange),
          title: Text(f, style: const TextStyle(fontSize: 11, color: AppColors.textPrimary)),
        )).toList(),
      ),
    );
  }

  // ── LOGIC XỬ LÝ CHO CHỌN VÀ UPLOAD FILE RM (DATABASE CONNECTED) ──────────
  void _pickLocalFile() {
    // Giả lập mở hộp thoại tệp tin của máy tính
    final sampleFiles = ['hop_dong_tin_dung.pdf', 'bao_cao_kiem_toan_2025.xlsx', 'to_trinh_tai_san_dam_bao.pdf', 'phu_luc_hop_dong.docx'];
    final pick = sampleFiles[(_localFiles.length) % sampleFiles.length];
    if (!_localFiles.contains(pick)) {
      setState(() {
        _localFiles.add(pick);
      });
    }
  }

  Future<void> _handleUploadDocuments() async {
    if (_selectedCaseId == null) return;
    setState(() {
      _isUploadingDocs = true;
    });

    try {
      final docNames = [..._localFiles, ..._selectedDocTypes.keys.where((k) => _selectedDocTypes[k] == true)];
      
      // Gọi API tải tài liệu lên Database (thông qua Backend API)
      await _salesCaseController.api.uploadDocuments(_selectedCaseId!, {
        'document_names': docNames,
      });

      // Kích hoạt xử lý tài liệu thông minh
      await _salesCaseController.api.processDocuments(_selectedCaseId!, docIds: []);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Đã tải và xử lý xong tài liệu cho hồ sơ $_selectedCaseId thành công! Dữ liệu đã lưu vào DB.'),
            backgroundColor: AppColors.success,
          ),
        );
        setState(() {
          _localFiles.clear();
        });
        await _salesCaseController.loadCases(); // Refresh danh sách hồ sơ từ DB
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi upload: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      setState(() {
        _isUploadingDocs = false;
      });
    }
  }

  // ── WIDGET CHATBOT AI VỚI "LUỒNG SUY NGHĨ" XOAY TRÒN & NÚT MŨI TÊN ──────────
  Widget _buildThinkingBubble() {
    return Align(
      alignment: Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.border),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.orange),
            ),
            const SizedBox(width: 10),
            Text(
              'AI đang phân tích & suy nghĩ...',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary, fontStyle: FontStyle.italic),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChatBubble(ChatMessage msg) {
    final isAi = msg.sender == 'ai';
    return Align(
      alignment: isAi ? Alignment.centerLeft : Alignment.centerRight,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: const BoxConstraints(maxWidth: 580),
        child: Column(
          crossAxisAlignment: isAi ? CrossAxisAlignment.start : CrossAxisAlignment.end,
          children: [
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: isAi ? Colors.white : AppColors.orange,
                borderRadius: BorderRadius.only(
                  topLeft: const Radius.circular(16),
                  topRight: const Radius.circular(16),
                  bottomLeft: isAi ? Radius.zero : const Radius.circular(16),
                  bottomRight: isAi ? const Radius.circular(16) : Radius.zero,
                ),
                border: isAi ? Border.all(color: AppColors.border) : null,
                boxShadow: [
                  BoxShadow(color: Colors.black.withValues(alpha: 0.04), blurRadius: 4, offset: const Offset(0, 2)),
                ],
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    msg.text,
                    style: TextStyle(
                      fontSize: 13,
                      color: isAi ? AppColors.textPrimary : Colors.white,
                      height: 1.4,
                    ),
                  ),
                  
                  // Phần luồng suy nghĩ của AI nếu có
                  if (isAi && msg.thinkingSteps != null && msg.thinkingSteps!.isNotEmpty) ...[
                    const Divider(height: 16),
                    Row(
                      children: [
                        const Icon(Icons.analytics_outlined, size: 14, color: AppColors.orange),
                        const SizedBox(width: 6),
                        Text(
                          'Luồng suy nghĩ AI',
                          style: GoogleFonts.beVietnamPro(fontSize: 10.5, fontWeight: FontWeight.bold, color: AppColors.orange),
                        ),
                        const Spacer(),
                        InkWell(
                          onTap: () {
                            setState(() {
                              msg.isExpanded = !msg.isExpanded;
                            });
                          },
                          child: Icon(
                            msg.isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                            size: 16,
                            color: AppColors.orange,
                          ),
                        ),
                      ],
                    ),
                    if (msg.isExpanded) ...[
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: AppColors.orangeBackground,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: msg.thinkingSteps!.map((step) => Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('• ', style: TextStyle(color: AppColors.orange, fontSize: 12, fontWeight: FontWeight.bold)),
                                Expanded(
                                  child: Text(
                                    step,
                                    style: GoogleFonts.jetBrainsMono(fontSize: 9.5, color: AppColors.textSecondary),
                                  ),
                                ),
                              ],
                            ),
                          )).toList(),
                        ),
                      ),
                    ],
                  ],
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.only(top: 4, left: 4, right: 4),
              child: Text(
                isAi ? 'Copilot AI' : 'Bạn',
                style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _handleSendChatMessage() {
    final query = _chatInput.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _chatHistory.add(ChatMessage(sender: 'user', text: query));
      _chatInput.clear();
      _aiThinking = true;
    });

    // Giả lập AI phân tích luồng suy nghĩ
    Future.delayed(const Duration(milliseconds: 1800), () {
      if (!mounted) return;
      
      String aiResponse = 'Tôi đã nhận được yêu cầu. Dựa trên hồ sơ của doanh nghiệp trong cơ sở dữ liệu, ';
      List<String> steps = [];

      if (query.toLowerCase().contains('hồ sơ') || query.toLowerCase().contains('case')) {
        steps = [
          'Phân tích ngữ nghĩa câu hỏi: Người dùng hỏi về danh sách hoặc chi tiết hồ sơ.',
          'Kết nối SQLite Database, truy vấn bảng `sales_cases`...',
          'Tìm thấy ${_salesCaseController.cases.length} hồ sơ đang được lưu trong Database.',
          'Đối chiếu trạng thái của khách hàng được phân công...',
          'Hoàn tất phân tích. Tạo báo cáo tóm tắt trạng thái gửi lại RM.',
        ];
        aiResponse += 'hệ thống hiện tại ghi nhận có ${_salesCaseController.cases.length} hồ sơ trong Database. Để phân tích chi tiết hồ sơ nào, vui lòng nhấp chọn hồ sơ đó ở cột bên trái hoặc cung cấp Mã hồ sơ.';
      } else if (query.toLowerCase().contains('hạn mức') || query.toLowerCase().contains('tín dụng')) {
        steps = [
          'Nhận dạng từ khóa: "hạn mức", "tín dụng".',
          'Truy vấn quy định sản phẩm tín dụng và điều kiện tài sản bảo đảm...',
          'Tính toán hệ số rủi ro SLA dựa trên lịch sử hoạt động doanh nghiệp.',
          'Tính toán biên độ tín dụng đề xuất tối đa là 15 tỷ VND.',
        ];
        aiResponse += 'khuyến nghị hạn mức tối đa đề xuất là 15 tỷ VNĐ dựa trên lịch sử doanh thu và dòng tiền của doanh nghiệp, tỷ lệ nợ/vốn chủ sở hữu vẫn nằm trong mức an toàn (dưới 3.0).';
      } else {
        steps = [
          'Phân tích câu hỏi tự do của RM.',
          'Đối chiếu cơ sở tri thức sản phẩm SHB (Product RAG MCP Server)...',
          'Truy xuất tài liệu hướng dẫn nghiệp vụ thẩm định doanh nghiệp...',
          'Tổng hợp câu trả lời tư vấn nghiệp vụ.',
        ];
        aiResponse += 'tôi đề xuất bạn nên kiểm tra kỹ báo cáo tài chính năm gần nhất của doanh nghiệp để thẩm định hệ số thanh toán nhanh và các khoản nợ ngắn hạn trước khi chuyển hồ sơ cho Risk Gate phê duyệt.';
      }

      setState(() {
        _aiThinking = false;
        _chatHistory.add(ChatMessage(sender: 'ai', text: aiResponse, thinkingSteps: steps));
      });
    });
  }
}

class ChatMessage {
  final String sender; // 'user' | 'ai'
  final String text;
  final List<String>? thinkingSteps;
  bool isExpanded;

  ChatMessage({
    required this.sender,
    required this.text,
    this.thinkingSteps,
    this.isExpanded = false,
  });
}
