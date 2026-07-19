import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/rm_workspace_core.dart';
import '../../design/design.dart';
import '../../design/theme/app_theme.dart';
import '../../design/widgets/agent_os.dart';
import '../../design/widgets/nav_sidebar.dart';

/// Customer portal — submits intake, tracks own case (COMP-MP) in 5/5 layout.
class CustomerWorkspaceScreen extends StatefulWidget {
  const CustomerWorkspaceScreen({super.key});

  @override
  State<CustomerWorkspaceScreen> createState() => _CustomerWorkspaceScreenState();
}

class _CustomerWorkspaceScreenState extends State<CustomerWorkspaceScreen> {
  final _company = TextEditingController(text: 'Minh Phát JSC');
  final _tax = TextEditingController(text: '0305123456');
  final _need = TextEditingController();
  late final SalesCaseController _controller;

  // Selected local files for customer upload
  final List<String> _selectedFiles = [];
  bool _isSubmitting = false;

  // Chatbot State variables
  final TextEditingController _chatInput = TextEditingController();
  final List<ChatMessage> _chatHistory = [
    ChatMessage(
      sender: 'ai',
      text: 'Xin chào quý khách! Tôi là trợ lý AI tự động hỗ trợ doanh nghiệp nộp và thẩm định hồ sơ tín dụng. Quý khách cần hỗ trợ giải đáp thông tin gì?',
      thinkingSteps: [
        'Kết nối trợ lý cổng thông tin khách hàng...',
        'Truy vấn quy chế sản phẩm cấp tín dụng doanh nghiệp nhỏ và vừa...',
        'Hệ thống sẵn sàng hỗ trợ khách hàng nộp hồ sơ.',
      ],
    ),
  ];
  bool _aiThinking = false;

  @override
  void initState() {
    super.initState();
    _controller = SalesCaseController(
      apiClient: context.read<EmployeeWorkspaceController>().api,
    );
    _controller.loadCases();
  }

  @override
  void dispose() {
    _company.dispose();
    _tax.dispose();
    _need.dispose();
    _chatInput.dispose();
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider.value(
      value: _controller,
      child: Consumer<EmployeeWorkspaceController>(
        builder: (context, emp, _) => Scaffold(
          backgroundColor: AppColors.background,
          drawer: Drawer(
            child: SafeArea(
              child: NavSidebar(
                current: 'customer',
                employeeId: emp.context?.employeeId ?? 'KH',
                roleLabel: 'Customer',
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
                  'CỔNG THÔNG TIN KHÁCH HÀNG DOANH NGHIỆP',
                  style: GoogleFonts.beVietnamPro(fontSize: 14, fontWeight: FontWeight.w900),
                ),
                const Text(
                  'Nộp hồ sơ trực tuyến · Hỗ trợ tư vấn AI',
                  style: TextStyle(fontSize: 10, color: Colors.white70),
                ),
              ],
            ),
            actions: [
              IconButton(
                icon: const Icon(Icons.logout),
                onPressed: () {
                  emp.logout();
                  context.go('/login');
                },
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: Row(
            children: [
              // ── 5/10 BÊN TRÁI: ĐIỀN THÔNG TIN & TẢI TÀI LIỆU LÊN DATABASE ──
              Expanded(
                flex: 5,
                child: Container(
                  decoration: const BoxDecoration(
                    color: Colors.white,
                    border: Border(right: BorderSide(color: AppColors.border, width: 1.5)),
                  ),
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'THÔNG TIN HỒ SƠ YÊU CẦU',
                          style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 15, color: AppColors.orangeDark),
                        ),
                        const SizedBox(height: 16),
                        
                        // Form nhập liệu thông tin doanh nghiệp
                        TextField(
                          controller: _company,
                          style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'BeVietnamPro'),
                          decoration: const InputDecoration(
                            labelText: 'Tên doanh nghiệp',
                            prefixIcon: Icon(Icons.business_outlined, color: AppColors.orange),
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _tax,
                          style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'BeVietnamPro'),
                          decoration: const InputDecoration(
                            labelText: 'Mã số thuế',
                            prefixIcon: Icon(Icons.tag_outlined, color: AppColors.orange),
                          ),
                        ),
                        const SizedBox(height: 12),
                        TextField(
                          controller: _need,
                          maxLines: 2,
                          style: const TextStyle(color: AppColors.textPrimary, fontSize: 13, fontFamily: 'BeVietnamPro'),
                          decoration: const InputDecoration(
                            labelText: 'Nhu cầu tín dụng / Sản phẩm mong muốn',
                            prefixIcon: Icon(Icons.edit_note_outlined, color: AppColors.orange),
                          ),
                        ),
                        
                        const Divider(height: 32, thickness: 1.2),
                        
                        // Phần tài liệu đính kèm từ doanh nghiệp
                        Row(
                          children: [
                            const Icon(Icons.upload_file_outlined, color: AppColors.textSecondary, size: 18),
                            const SizedBox(width: 8),
                            Text(
                              'ĐÍNH KÈM TÀI LIỆU CỦA DOANH NGHIỆP',
                              style: GoogleFonts.beVietnamPro(fontSize: 11, fontWeight: FontWeight.bold, color: AppColors.textSecondary),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        InkWell(
                          onTap: _pickLocalFile,
                          child: Container(
                            height: 75,
                            width: double.infinity,
                            decoration: BoxDecoration(
                              color: AppColors.orangeBackground,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: AppColors.orange.withValues(alpha: 0.5)),
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(Icons.add_circle_outline, color: AppColors.orange, size: 20),
                                const SizedBox(height: 4),
                                Text(
                                  'Tải lên tài liệu đính kèm (BCTC, Giấy ĐKKD...)',
                                  style: GoogleFonts.beVietnamPro(fontSize: 10.5, color: AppColors.orangeDark, fontWeight: FontWeight.w600),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        if (_selectedFiles.isNotEmpty) ...[
                          Container(
                            decoration: BoxDecoration(
                              color: AppColors.orangeBackground,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.border),
                            ),
                            child: Column(
                              children: _selectedFiles.map((file) => ListTile(
                                dense: true,
                                visualDensity: VisualDensity.compact,
                                leading: const Icon(Icons.insert_drive_file, size: 16, color: AppColors.orange),
                                title: Text(file, style: const TextStyle(fontSize: 11)),
                                trailing: IconButton(
                                  icon: const Icon(Icons.delete_outline, size: 16, color: AppColors.error),
                                  onPressed: () => setState(() => _selectedFiles.remove(file)),
                                ),
                              )).toList(),
                            ),
                          ),
                          const SizedBox(height: 16),
                        ],

                        if (_controller.error != null) ...[
                          Container(
                            padding: const EdgeInsets.all(10),
                            decoration: BoxDecoration(
                              color: AppColors.blockBg,
                              borderRadius: BorderRadius.circular(10),
                              border: Border.all(color: AppColors.block.withValues(alpha: 0.5)),
                            ),
                            child: Text(_controller.error!, style: const TextStyle(color: AppColors.block, fontSize: 12)),
                          ),
                          const SizedBox(height: 12),
                        ],
                        
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: _controller.isBusy || _isSubmitting ? null : _submitCaseAndFiles,
                            icon: const Icon(Icons.send),
                            style: FilledButton.styleFrom(
                              backgroundColor: AppColors.orange,
                              padding: const EdgeInsets.symmetric(vertical: 14),
                            ),
                            label: Text(_controller.isBusy || _isSubmitting ? 'Đang gửi hồ sơ...' : 'Gửi yêu cầu & Tài liệu'),
                          ),
                        ),

                        const Divider(height: 40, thickness: 1.2),

                        // Danh sách hồ sơ đã gửi để theo dõi trạng thái
                        Text(
                          'HỒ SƠ CỦA BẠN TRÊN HỆ THỐNG',
                          style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 12, color: AppColors.textSecondary),
                        ),
                        const SizedBox(height: 12),
                        _buildMyCasesList(),
                      ],
                    ),
                  ),
                ),
              ),
              
              // ── 5/10 BÊN PHẢI: CHATBOT AI VỚI LUỒNG SUY NGHĨ VÀ MŨI TÊN ──
              Expanded(
                flex: 5,
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
                              child: const Icon(Icons.forum_outlined, color: AppColors.orange, size: 22),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'AI CONSULTANT',
                                    style: GoogleFonts.beVietnamPro(fontWeight: FontWeight.w900, fontSize: 14, color: AppColors.orangeDark),
                                  ),
                                  const Text('Giải đáp thắc mắc thủ tục và sản phẩm tín dụng tự động', style: TextStyle(fontSize: 11, color: AppColors.textSecondary)),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),

                      // Danh sách tin nhắn chat
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

                      // Ô nhập chat
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
                                  hintText: 'Nhập câu hỏi cần tư vấn thủ tục, gói tín dụng...',
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
          ),
        ),
      ),
    );
  }

  // Logic chọn tài liệu giả lập
  void _pickLocalFile() {
    final sampleFiles = ['GPDKKD_MinhPhat.pdf', 'BCTC_MinhPhat_2024.xlsx', 'ToTrinh_MinhPhat.pdf', 'XacNhanThue.pdf'];
    final pick = sampleFiles[(_selectedFiles.length) % sampleFiles.length];
    if (!_selectedFiles.contains(pick)) {
      setState(() {
        _selectedFiles.add(pick);
      });
    }
  }

  // Gửi thông tin hồ sơ và upload tài liệu trực tiếp vào Database
  Future<void> _submitCaseAndFiles() async {
    final name = _company.text.trim();
    final tax = _tax.text.trim();
    final need = _need.text.trim();

    if (name.isEmpty || need.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng điền đầy đủ tên doanh nghiệp và nhu cầu tín dụng'), backgroundColor: AppColors.error),
      );
      return;
    }

    setState(() {
      _isSubmitting = true;
    });

    try {
      // 1. Tạo case mới trên Database
      await _controller.createCase(
        companyName: name,
        taxCode: tax,
        needText: need,
      );

      // Lấy caseId vừa tạo từ controller
      final createdCaseId = _controller.activeId;
      if (createdCaseId != null && createdCaseId.isNotEmpty) {
        // 2. Upload tài liệu đính kèm vào Database nếu có
        if (_selectedFiles.isNotEmpty) {
          await _controller.api.uploadDocuments(createdCaseId, {
            'document_names': _selectedFiles,
          });
          // Kích hoạt xử lý tài liệu AI
          await _controller.api.processDocuments(createdCaseId, docIds: []);
        }

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Đã gửi yêu cầu hồ sơ ($createdCaseId) và tải tài liệu lên Database thành công!'),
              backgroundColor: AppColors.success,
            ),
          );
          setState(() {
            _selectedFiles.clear();
            _need.clear();
          });
          await _controller.loadCases(); // Refresh danh sách hồ sơ
        }
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Gửi hồ sơ thất bại: $e'), backgroundColor: AppColors.error),
        );
      }
    } finally {
      setState(() {
        _isSubmitting = false;
      });
    }
  }

  Widget _buildMyCasesList() {
    return ListenableBuilder(
      listenable: _controller,
      builder: (context, _) {
        if (_controller.isLoading) {
          return const Center(child: Padding(padding: EdgeInsets.all(12), child: CircularProgressIndicator(color: AppColors.orange)));
        }
        if (_controller.cases.isEmpty) {
          return Container(
            padding: const EdgeInsets.all(16),
            alignment: Alignment.center,
            decoration: BoxDecoration(color: Colors.grey[50], borderRadius: BorderRadius.circular(8), border: Border.all(color: AppColors.border)),
            child: const Text('Chưa có hồ sơ nào được gửi lên.', style: TextStyle(fontSize: 11, color: AppColors.textDisabled, fontStyle: FontStyle.italic)),
          );
        }

        return Column(
          children: _controller.cases.map((c) {
            final caseId = (c['case_id'] ?? '').toString();
            final companyName = (c['company_name'] ?? c['customer_id'] ?? 'Doanh nghiệp').toString();
            final status = (c['intake_status'] ?? 'draft').toString();

            return Container(
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: AppColors.border),
              ),
              child: ListTile(
                dense: true,
                visualDensity: VisualDensity.compact,
                leading: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(color: AppColors.orangeLight, borderRadius: BorderRadius.circular(8)),
                  child: const Center(child: Icon(Icons.folder_open, color: AppColors.orange, size: 16)),
                ),
                title: Text(companyName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: AppColors.textPrimary)),
                subtitle: Text('ID: $caseId', style: GoogleFonts.jetBrainsMono(fontSize: 9.5, color: AppColors.textSecondary)),
                trailing: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(color: AppColors.orange.withValues(alpha: 0.12), borderRadius: BorderRadius.circular(8)),
                  child: Text(status.toUpperCase(), style: const TextStyle(fontSize: 9, fontWeight: FontWeight.bold, color: AppColors.orange)),
                ),
              ),
            );
          }).toList(),
        );
      },
    );
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
              'Trợ lý AI đang tra cứu...',
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
        constraints: const BoxConstraints(maxWidth: 420),
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
                isAi ? 'Trợ lý AI' : 'Quý khách',
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
      
      String aiResponse = 'Cảm ơn quý khách đã gửi yêu cầu tư vấn. ';
      List<String> steps = [];

      if (query.toLowerCase().contains('thủ tục') || query.toLowerCase().contains('hồ sơ') || query.toLowerCase().contains('giấy tờ')) {
        steps = [
          'Đọc hiểu ý định của khách hàng: hỏi về hồ sơ, thủ tục.',
          'Đối chiếu cơ sở dữ liệu các loại hồ sơ tín dụng mẫu...',
          'Tìm kiếm điều kiện về Báo cáo tài chính, Giấy phép ĐKKD.',
          'Biên soạn danh mục hướng dẫn chi tiết cho doanh nghiệp nhỏ và vừa.',
        ];
        aiResponse += 'Để hoàn thành thủ tục đề xuất hạn mức tín dụng, doanh nghiệp của quý khách cần chuẩn bị tối thiểu: (1) Giấy đăng ký kinh doanh hợp lệ, (2) Báo cáo tài chính 3 năm gần nhất (hoặc tờ khai VAT 12 tháng gần nhất), và (3) Phương án sử dụng vốn kinh doanh.';
      } else if (query.toLowerCase().contains('gói') || query.toLowerCase().contains('sản phẩm') || query.toLowerCase().contains('lãi suất')) {
        steps = [
          'Nhận dạng từ khóa: "lãi suất", "sản phẩm tín dụng".',
          'Truy vấn danh mục sản phẩm của SHB (Product Catalog)...',
          'Tìm thấy chương trình ưu đãi lãi suất quý hiện hành cho doanh nghiệp SMEs.',
          'Tính toán lãi suất đề xuất cơ sở.',
        ];
        aiResponse += 'SHB hiện đang có gói tín dụng hỗ trợ SMEs với lãi suất ưu đãi chỉ từ 5.5%/năm cho vay ngắn hạn bổ sung vốn lưu động, và thời gian duyệt hồ sơ siêu tốc trong 24h làm việc.';
      } else {
        steps = [
          'Phân tích ngữ cảnh tự do từ khách hàng.',
          'Tra cứu RAG tri thức tín dụng doanh nghiệp...',
          'Định hình hướng giải quyết và phản hồi hỗ trợ.',
        ];
        aiResponse += 'Để được tư vấn chính xác nhất về gói vay cũng như hạn mức phù hợp cho doanh nghiệp của mình, quý khách vui lòng nhập đầy đủ thông tin vào Form bên trái và nhấn gửi hồ sơ, RM sẽ liên hệ hỗ trợ quý khách ngay lập tức.';
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
