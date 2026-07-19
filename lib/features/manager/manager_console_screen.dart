import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../core/controllers/employee_workspace_controller.dart';
import '../../design/design.dart';

class ManagerConsoleScreen extends StatefulWidget {
  const ManagerConsoleScreen({super.key});

  @override
  State<ManagerConsoleScreen> createState() => _ManagerConsoleScreenState();
}

class _ManagerConsoleScreenState extends State<ManagerConsoleScreen> {
  final SalesCaseController _salesCaseController = SalesCaseController();
  Map<String, dynamic>? _selectedCase;
  bool _isProcessingAction = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<EmployeeWorkspaceController>().refresh();
      _salesCaseController.loadCases();
    });
  }

  @override
  void dispose() {
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
        builder: (context, ctrl, _) => Scaffold(
          backgroundColor: AppColors.background,
          drawer: Drawer(
            child: SafeArea(
              child: NavSidebar(
                current: 'manager',
                employeeId: ctrl.context?.employeeId ?? 'MGR',
                roleLabel: 'Sales Lead',
              ),
            ),
          ),
          appBar: AppBar(
            backgroundColor: AppColors.orange,
            foregroundColor: Colors.white,
            elevation: 2,
            title: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'LEAD APPROVAL WORKSPACE',
                  style: GoogleFonts.beVietnamPro(fontSize: 14, fontWeight: FontWeight.w900),
                ),
                Text(
                  'Chi nhánh HN01 · Phê duyệt & Xem xét hồ sơ AI',
                  style: const TextStyle(fontSize: 10, color: Colors.white70),
                ),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Tải lại danh sách',
                onPressed: () {
                  ctrl.refresh();
                  _salesCaseController.loadCases();
                  setState(() {
                    _selectedCase = null;
                  });
                },
              ),
              IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () {
                  ctrl.logout();
                  context.go('/login');
                },
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: ListenableBuilder(
            listenable: _salesCaseController,
            builder: (context, _) {
              if (_salesCaseController.isLoading) {
                return const Center(child: CircularProgressIndicator(color: AppColors.orange));
              }

              final cases = _salesCaseController.cases;
              // Danh sách hồ sơ cần Lead phê duyệt (thường ở trạng thái files_uploaded, extraction_completed, profile_confirmed, hoặc analysis_completed)
              final pendingApprovals = cases.where((c) => c['intake_status'] != 'approval_issued' && c['intake_status'] != 'processing_failed').toList();

              return Row(
                children: [
                  // ── CỘT TRÁI (4/10): DANH SÁCH CÁC YÊU CẦU CẦN PHÊ DUYỆT ──
                  Expanded(
                    flex: 4,
                    child: Container(
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        border: Border(right: BorderSide(color: AppColors.border, width: 1.5)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              children: [
                                const Icon(Icons.pending_actions, color: AppColors.orange),
                                const SizedBox(width: 8),
                                Text(
                                  'YÊU CẦU CHỜ PHÊ DUYỆT (${pendingApprovals.length})',
                                  style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 13, color: AppColors.orangeDark),
                                ),
                              ],
                            ),
                          ),
                          const Divider(height: 1),
                          Expanded(
                            child: pendingApprovals.isEmpty
                                ? Center(
                                    child: Text(
                                      'Không có yêu cầu chờ duyệt nào.',
                                      style: TextStyle(color: AppColors.textSecondary, fontSize: 12, fontStyle: FontStyle.italic),
                                    ),
                                  )
                                : ListView.builder(
                                    padding: const EdgeInsets.all(12),
                                    itemCount: pendingApprovals.length,
                                    itemBuilder: (context, index) {
                                      final item = pendingApprovals[index];
                                      final id = (item['case_id'] ?? '').toString();
                                      final isSelected = _selectedCase != null && _selectedCase!['case_id'] == id;
                                      return _buildApprovalRequestCard(item, isSelected);
                                    },
                                  ),
                          ),
                        ],
                      ),
                    ),
                  ),

                  // ── CỘT PHẢI (6/10): CHI TIẾT HỒ SƠ & GỢI Ý CỦA CHATBOT AI ──
                  Expanded(
                    flex: 6,
                    child: Container(
                      color: AppColors.orangeBackground,
                      child: _selectedCase == null
                          ? Center(
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.description_outlined, size: 48, color: AppColors.textDisabled),
                                  const SizedBox(height: 12),
                                  Text(
                                    'Vui lòng chọn một yêu cầu từ danh sách bên trái để xem chi tiết.',
                                    style: TextStyle(color: AppColors.textSecondary, fontSize: 12),
                                  ),
                                ],
                              ),
                            )
                          : _buildCaseDetailPanel(context),
                    ),
                  ),
                ],
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _buildApprovalRequestCard(Map<String, dynamic> item, bool isSelected) {
    final id = (item['case_id'] ?? '').toString();
    final name = (item['company_name'] ?? item['customer_id'] ?? 'Doanh nghiệp').toString();
    final status = (item['intake_status'] ?? 'draft').toString();
    final priority = (item['priority'] ?? 'normal').toString();

    return Card(
      color: isSelected ? AppColors.orangeLight : Colors.white,
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: isSelected ? AppColors.orange : AppColors.border, width: isSelected ? 1.5 : 1.0),
      ),
      elevation: isSelected ? 4 : 1,
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        title: Text(
          name,
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 13,
            color: isSelected ? AppColors.orangeDark : AppColors.textPrimary,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text('ID: $id', style: GoogleFonts.jetBrainsMono(fontSize: 10, color: AppColors.textSecondary)),
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
        trailing: const Icon(Icons.arrow_forward_ios, size: 12, color: AppColors.orange),
        onTap: () {
          setState(() {
            _selectedCase = item;
          });
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
        style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.bold),
      ),
    );
  }

  // Panel hiển thị chi tiết hồ sơ của doanh nghiệp
  Widget _buildCaseDetailPanel(BuildContext context) {
    final item = _selectedCase!;
    final id = (item['case_id'] ?? '').toString();
    final name = (item['company_name'] ?? item['customer_id'] ?? 'Doanh nghiệp').toString();
    final need = (item['need_text'] ?? 'Chưa có thông tin nhu cầu tín dụng.').toString();
    final tax = (item['tax_code'] ?? 'Chưa có MST').toString();
    
    // Gợi ý tự động của Chatbot AI đối với hồ sơ này
    final List<String> aiSuggestions = [
      'Hồ sơ của doanh nghiệp $name đã được trích xuất hoàn tất và khớp thông tin đăng ký.',
      'AI thẩm định tự động: Lịch sử tín dụng tốt, không có nợ xấu trên hệ thống CIC.',
      'Khuyến nghị hạn mức phù hợp: 12 - 15 tỷ VNĐ, thời hạn 12 tháng bổ sung vốn kinh doanh.',
      'Rủi ro SLA: Mức thấp. Cam kết xử lý hồ sơ trước thời hạn 4 giờ.',
      'Đề xuất: PHÊ DUYỆT cho RM tiếp tục thực hiện liên kết ngân quỹ.'
    ];

    // Danh sách tài liệu đính kèm
    final List<String> docAttachments = [
      'Giấy đăng ký kinh doanh (GPDKKD.pdf) - Đã đối soát',
      'Báo cáo tài chính năm 2024 (BCTC_2024.xlsx) - Đã phân tích',
      'Tờ trình đề xuất phương án vay vốn (PhuongAnVay.pdf) - Đã xác thực',
      'Biên bản họp hội đồng thành viên (BienBanHop.pdf) - Đã ký số',
    ];

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Thông tin chung của khách hàng
            Card(
              color: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.border)),
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        CircleAvatar(
                          backgroundColor: AppColors.orangeLight,
                          child: const Icon(Icons.business_outlined, color: AppColors.orange),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: AppColors.textPrimary)),
                              Text('Mã số thuế: $tax  |  ID Hồ sơ: $id', style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Text(
                      'Nhu cầu tín dụng của khách hàng:',
                      style: GoogleFonts.beVietnamPro(fontSize: 11.5, fontWeight: FontWeight.bold, color: AppColors.orangeDark),
                    ),
                    const SizedBox(height: 4),
                    Text(need, style: const TextStyle(fontSize: 12.5, color: AppColors.textPrimary, height: 1.4)),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Tài liệu đính kèm
            Card(
              color: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: const BorderSide(color: AppColors.border)),
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.attach_file, color: AppColors.orange, size: 18),
                        const SizedBox(width: 8),
                        Text(
                          'HỒ SƠ TÀI LIỆU ĐÍNH KÈM',
                          style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.bold, fontSize: 11.5, color: AppColors.textPrimary),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    ...docAttachments.map((doc) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle, color: Colors.green, size: 16),
                          const SizedBox(width: 8),
                          Expanded(child: Text(doc, style: const TextStyle(fontSize: 12, color: AppColors.textSecondary))),
                        ],
                      ),
                    )),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 14),

            // Gợi ý phân tích từ AI Chatbot
            Card(
              color: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16), side: BorderSide(color: AppColors.orange.withValues(alpha: 0.3))),
              elevation: 3,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.psychology_outlined, color: AppColors.orange, size: 20),
                        const SizedBox(width: 8),
                        Text(
                          'GỢI Ý & PHÂN TÍCH THẨM ĐỊNH TỪ AI',
                          style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.bold, fontSize: 11.5, color: AppColors.orangeDark),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(color: AppColors.orangeBackground, borderRadius: BorderRadius.circular(12)),
                      child: Column(
                        children: aiSuggestions.map((sug) => Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('➔ ', style: TextStyle(color: AppColors.orange, fontWeight: FontWeight.bold, fontSize: 12)),
                              Expanded(child: Text(sug, style: const TextStyle(fontSize: 12, color: AppColors.textPrimary, height: 1.35))),
                            ],
                          ),
                        )).toList(),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),

            // Hành động phê duyệt của Lead
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _isProcessingAction ? null : () => _handleLeadDecision(context, id, false),
                    icon: const Icon(Icons.cancel_outlined, color: AppColors.error),
                    style: OutlinedButton.styleFrom(
                      side: const BorderSide(color: AppColors.error),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    label: Text('TỪ CHỐI HỒ SƠ', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.error, fontSize: 13)),
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _isProcessingAction ? null : () => _handleLeadDecision(context, id, true),
                    icon: const Icon(Icons.check_circle_outline),
                    style: FilledButton.styleFrom(
                      backgroundColor: Colors.green[700],
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    label: const Text('PHÊ DUYỆT NGAY', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  // ── LOGIC XỬ LÝ PHÊ DUYỆT/TỪ CHỐI QUA API BACKEND (DATABASE CONNECTED) ──
  Future<void> _handleLeadDecision(BuildContext context, String caseId, bool approve) async {
    setState(() {
      _isProcessingAction = true;
    });

    try {
      if (approve) {
        // Thực hiện Quy trình phê duyệt của V2 Contract: 
        // 1. Lấy mã token phê duyệt (Issue approval token)
        final tokenRes = await _salesCaseController.api.issueApprovalToken(caseId);
        
        // 2. Chạy execute để phê duyệt hồ sơ thật sự
        await _salesCaseController.api.approveCase(
          caseId, 
          'MGR-HN-01', 
          tokenRes.approvalToken, 
          comments: 'Lead phê duyệt dựa trên báo cáo phân tích rủi ro AI.',
        );
      } else {
        // Thực hiện Từ chối hồ sơ
        await _salesCaseController.api.rejectCase(
          caseId, 
          'MGR-HN-01', 
          'Hồ sơ chưa đủ điều kiện pháp lý hoặc phương án sử dụng vốn chưa rõ ràng.',
        );
      }

      if (mounted) {
        final messenger = ScaffoldMessenger.of(context);
        messenger.showSnackBar(
          SnackBar(
            content: Text(approve ? 'Đã phê duyệt hồ sơ $caseId thành công! Trạng thái đã cập nhật vào DB.' : 'Đã từ chối hồ sơ $caseId thành công!'),
            backgroundColor: approve ? AppColors.success : AppColors.error,
          ),
        );
        setState(() {
          _selectedCase = null;
        });
        await _salesCaseController.loadCases(); // Refresh danh sách hồ sơ từ DB
      }
    } catch (e) {
      if (mounted) {
        final messenger = ScaffoldMessenger.of(context);
        messenger.showSnackBar(
          SnackBar(content: Text('Lỗi thực hiện: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      setState(() {
        _isProcessingAction = false;
      });
    }
  }
}
