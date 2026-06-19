import 'dart:ui' show PlatformDispatcher;
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:hive_flutter/hive_flutter.dart';
import 'core/theme/app_theme.dart';
import 'core/blocs/dashboard/dashboard_cubit.dart';
import 'core/blocs/portfolio/portfolio_cubit.dart';
import 'core/network/yahoo_finance_service.dart';
import 'core/analytics/darvax_scanner.dart';
import 'scanner/blocs/scanner_cubit.dart';
import 'analyzer/blocs/analyzer_cubit.dart';
import 'features/alerts/blocs/alerts_cubit.dart';
import 'features/dashboard/dashboard_screen.dart';
import 'features/portfolio/portfolio_screen.dart';
import 'features/settings/settings_screen.dart';
import 'analyzer/analyzer_screen.dart';
import 'scanner/scanner_screen.dart';
import 'features/alerts/alerts_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // ── Hive Initialisation (MUST run before any cubit accesses a box) ──
  await Hive.initFlutter();
  await Future.wait([
    Hive.openBox<String>('portfolio_holdings'),
    Hive.openBox<String>('alerts_data'),
  ]);

  final yahooService = YahooFinanceService();
  final scannerEngine = DarvaXScannerEngine(yahoo: yahooService);

  // ── Global Error Handler ────────────────────────────────────────────
  FlutterError.onError = (details) {
    FlutterError.presentError(details);
    debugPrint('[FATAL] ${details.exception}\n${details.stack}');
  };
  PlatformDispatcher.instance.onError = (error, stack) {
    debugPrint('[PLATFORM] $error\n$stack');
    return true;
  };

  runApp(DarvaXApp(
    yahooService: yahooService,
    scannerEngine: scannerEngine,
  ));
}

class DarvaXApp extends StatelessWidget {
  final YahooFinanceService yahooService;
  final DarvaXScannerEngine scannerEngine;

  const DarvaXApp({
    super.key,
    required this.yahooService,
    required this.scannerEngine,
  });

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => PortfolioCubit(yahoo: yahooService)),
        BlocProvider(create: (_) => ScannerCubit(scanner: scannerEngine)),
        BlocProvider(create: (_) => AnalyzerCubit(scanner: scannerEngine)),
        BlocProvider(create: (_) => AlertsCubit(yahoo: yahooService)),
        BlocProvider(
          create: (ctx) => DashboardCubit(
            yahooService: yahooService,
            portfolioCubit: ctx.read<PortfolioCubit>(),
          ),
        ),
      ],
      child: MaterialApp(
        title: 'DarvaX',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.build(),
        home: const MainShell(),
      ),
    );
  }
}

/// ─── Main Shell ─────────────────────────────────────────────────────────
/// Manages bottom navigation and provides a tab-switch callback to children.
///
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  void _onTabSelected(int index) {
    setState(() => _currentIndex = index);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          DashboardScreen(onNavigateToTab: _onTabSelected),
          const AnalyzerScreen(),
          PortfolioScreen(onNavigateToTab: _onTabSelected),
          const ScannerScreen(),
          const AlertsScreen(),
          const SettingsScreen(),
        ],
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0xFF23252A))),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: _onTabSelected,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.dashboard_rounded, size: 22),
              activeIcon: Icon(Icons.dashboard_rounded, size: 22),
              label: 'Dashboard',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.analytics_rounded, size: 22),
              activeIcon: Icon(Icons.analytics_rounded, size: 22),
              label: 'Analyze',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.account_balance_rounded, size: 22),
              activeIcon: Icon(Icons.account_balance_rounded, size: 22),
              label: 'Portfolio',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.radar_rounded, size: 22),
              activeIcon: Icon(Icons.radar_rounded, size: 22),
              label: 'Scanner',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.notifications_rounded, size: 22),
              activeIcon: Icon(Icons.notifications_rounded, size: 22),
              label: 'Alerts',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.settings_rounded, size: 22),
              activeIcon: Icon(Icons.settings_rounded, size: 22),
              label: 'Settings',
            ),
          ],
        ),
      ),
    );
  }
}
