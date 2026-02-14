import 'package:flutter/material.dart';
import 'home_page.dart';
import '../services/auth_service.dart';

class SignUpPage extends StatefulWidget {
  const SignUpPage({Key? key}) : super(key: key);

  @override
  State<SignUpPage> createState() => _SignUpPageState();
}

class _SignUpPageState extends State<SignUpPage> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _authService = AuthService();

  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _signUp() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final response = await _authService.signUp(
        name: _nameController.text.trim(),
        email: _emailController.text.trim(),
        password: _passwordController.text,
      );

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Account created successfully'),
            backgroundColor: Colors.green,
          ),
        );

        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const HomePage()),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('Exception: ', '');
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: LayoutBuilder(
        builder: (context, constraints) {
          return SingleChildScrollView(
            physics: const BouncingScrollPhysics(),
            keyboardDismissBehavior:
            ScrollViewKeyboardDismissBehavior.onDrag,
            child: ConstrainedBox(
              constraints: BoxConstraints(
                minHeight: constraints.maxHeight,
              ),
              child: IntrinsicHeight(
                child: Column(
                  children: [

                    /// ===== Header =====
                    Container(
                      width: double.infinity,
                      height: constraints.maxHeight * 0.35,
                      decoration: const BoxDecoration(
                        gradient: LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [
                            Color(0xFF64B5F6),
                            Color(0xFF4DD0E1),
                          ],
                        ),
                        borderRadius: BorderRadius.only(
                          bottomLeft: Radius.circular(30),
                          bottomRight: Radius.circular(30),
                        ),
                      ),
                      child: SafeArea(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Align(
                              alignment: Alignment.topLeft,
                              child: Padding(
                                padding: const EdgeInsets.only(
                                    left: 16, bottom: 20),
                                child: InkWell(
                                  onTap: () => Navigator.pop(context),
                                  borderRadius:
                                  BorderRadius.circular(20),
                                  child: Container(
                                    padding: const EdgeInsets.all(8),
                                    decoration: BoxDecoration(
                                      color: Colors.white
                                          .withOpacity(0.2),
                                      shape: BoxShape.circle,
                                    ),
                                    child: const Icon(
                                      Icons.arrow_back_rounded,
                                      color: Colors.white,
                                      size: 20,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            Container(
                              padding:
                              const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color:
                                Colors.white.withOpacity(0.2),
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(
                                Icons.person_add_rounded,
                                size: 48,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'Create Account',
                              style: TextStyle(
                                fontSize: 24,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              'Sign up to get started',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.white
                                    .withOpacity(0.9),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),

                    /// ===== Form =====
                    Expanded(
                      child: Padding(
                        padding:
                        const EdgeInsets.all(24.0),
                        child: Column(
                          children: [
                            const SizedBox(height: 24),

                            if (_errorMessage != null) ...[
                              Container(
                                padding: const EdgeInsets.all(16),
                                decoration: BoxDecoration(
                                  color: Colors.red.shade50,
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: Colors.red.shade200),
                                ),
                                child: Row(
                                  children: [
                                    Icon(Icons.error_outline, color: Colors.red.shade700),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Text(
                                        _errorMessage!,
                                        style: TextStyle(color: Colors.red.shade700),
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 20),
                            ],

                            _inputContainer(
                              context,
                              child: TextField(
                                controller:
                                _nameController,
                                decoration:
                                const InputDecoration(
                                  labelText: 'Full Name',
                                  prefixIcon:
                                  Icon(Icons.person_rounded),
                                  border: InputBorder.none,
                                  contentPadding:
                                  EdgeInsets.all(20),
                                ),
                              ),
                            ),

                            const SizedBox(height: 20),

                            _inputContainer(
                              context,
                              child: TextField(
                                controller:
                                _emailController,
                                decoration:
                                const InputDecoration(
                                  labelText:
                                  'Email Address',
                                  prefixIcon:
                                  Icon(Icons.email_rounded),
                                  border: InputBorder.none,
                                  contentPadding:
                                  EdgeInsets.all(20),
                                ),
                              ),
                            ),

                            const SizedBox(height: 20),

                            _inputContainer(
                              context,
                              child: TextField(
                                controller:
                                _passwordController,
                                obscureText: true,
                                decoration:
                                const InputDecoration(
                                  labelText: 'Password',
                                  prefixIcon:
                                  Icon(Icons.lock_rounded),
                                  border: InputBorder.none,
                                  contentPadding:
                                  EdgeInsets.all(20),
                                ),
                              ),
                            ),

                            const SizedBox(height: 32),

                            /// Button
                            SizedBox(
                              width: double.infinity,
                              height: 56,
                              child: InkWell(
                                onTap: _isLoading
                                    ? null
                                    : _signUp,
                                borderRadius:
                                BorderRadius.circular(
                                    16),
                                child: Container(
                                  decoration:
                                  BoxDecoration(
                                    gradient:
                                    LinearGradient(
                                      colors: _isLoading
                                          ? [
                                        Colors.grey
                                            .shade400,
                                        Colors.grey
                                            .shade500
                                      ]
                                          : const [
                                        Color(
                                            0xFF64B5F6),
                                        Color(
                                            0xFF4DD0E1)
                                      ],
                                    ),
                                    borderRadius:
                                    BorderRadius
                                        .circular(16),
                                  ),
                                  child: Center(
                                    child: _isLoading
                                        ? const CircularProgressIndicator(
                                      color: Colors
                                          .white,
                                    )
                                        : const Text(
                                      'Create Account',
                                      style:
                                      TextStyle(
                                        color: Colors
                                            .white,
                                        fontWeight:
                                        FontWeight
                                            .w600,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),

                            const SizedBox(height: 24),

                            Row(
                              mainAxisAlignment:
                              MainAxisAlignment
                                  .center,
                              children: [
                                Text(
                                  "Already have an account?",
                                  style: theme
                                      .textTheme
                                      .bodyMedium,
                                ),
                                TextButton(
                                  onPressed: _isLoading ? null : () =>
                                      Navigator.pop(
                                          context),
                                  child: const Text(
                                      'Sign In'),
                                ),
                              ],
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
        },
      ),

    );
  }

  /// ===== Input Container =====
  Widget _inputContainer(
      BuildContext context, {
        required Widget child,
      }) {
    final theme = Theme.of(context);

    return Container(
      decoration: BoxDecoration(
        color: theme.cardColor,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
          ),
        ],
      ),
      child: child,
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
}