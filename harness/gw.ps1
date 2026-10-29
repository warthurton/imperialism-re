# Test harness for the Imperialism mirror shim. Dot-source this file.
Add-Type -ReferencedAssemblies System.Drawing @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using System.Drawing;
using System.Drawing.Imaging;
public static class GW {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc p, IntPtr l);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern bool IsIconic(IntPtr h);
  [DllImport("user32.dll")] static extern bool IsZoomed(IntPtr h);
  [DllImport("user32.dll")] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
  [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
  [DllImport("user32.dll")] public static extern void mouse_event(uint f, uint dx, uint dy, uint d, UIntPtr e);
  [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int w, int hh, uint f);
  [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
  [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
  [StructLayout(LayoutKind.Sequential)] public struct CURSORINFO { public int cbSize, flags; public IntPtr hCursor; public POINT pt; }
  [DllImport("user32.dll")] static extern bool GetCursorInfo(ref CURSORINFO ci);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  public static long CursorHandle() { var ci = new CURSORINFO(); ci.cbSize = Marshal.SizeOf(typeof(CURSORINFO)); GetCursorInfo(ref ci); return ci.hCursor.ToInt64(); }
  public static void Key(byte vk) { keybd_event(vk, 0, 0, UIntPtr.Zero); System.Threading.Thread.Sleep(40); keybd_event(vk, 0, 2, UIntPtr.Zero); System.Threading.Thread.Sleep(60); }
  public static void KeyDown(byte vk) { keybd_event(vk, 0, 0, UIntPtr.Zero); }
  public static void KeyUp(byte vk) { keybd_event(vk, 0, 2, UIntPtr.Zero); }
  public static void Text(string s) { foreach (char c in s) { byte vk = (byte)char.ToUpper(c); bool shift = char.IsUpper(c); if (shift) KeyDown(0x10); Key(vk); if (shift) KeyUp(0x10); } }
  public static void Wheel(int delta) { mouse_event(0x0800, 0, 0, (uint)delta, UIntPtr.Zero); }
  public static void MouseDown() { mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero); }
  public static void MouseUp() { mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero); }
  public static void Drag(int x0, int y0, int x1, int y1) {
    SetCursorPos(x0, y0); System.Threading.Thread.Sleep(150); MouseDown(); System.Threading.Thread.Sleep(150);
    for (int i = 1; i <= 12; i++) { SetCursorPos(x0 + (x1 - x0) * i / 12, y0 + (y1 - y0) * i / 12); System.Threading.Thread.Sleep(40); }
    System.Threading.Thread.Sleep(150); MouseUp();
  }
  static GW() { SetProcessDPIAware(); }
  public static List<string[]> Windows(uint pid) {
    var res = new List<string[]>();
    EnumWindows((h, l) => {
      uint p; GetWindowThreadProcessId(h, out p);
      if (p != pid) return true;
      var c = new StringBuilder(128); GetClassName(h, c, 128);
      var t = new StringBuilder(128); GetWindowText(h, t, 128);
      RECT r; GetWindowRect(h, out r);
      res.Add(new[] { h.ToInt64().ToString(), c.ToString(), t.ToString(),
        IsWindowVisible(h) ? "vis" : "hid", IsIconic(h) ? "iconic" : "", IsZoomed(h) ? "zoomed" : "",
        string.Format("({0},{1} {2}x{3})", r.L, r.T, r.R - r.L, r.B - r.T) });
      return true;
    }, IntPtr.Zero);
    return res;
  }
  public static void Shot(IntPtr h, string path) {
    RECT r; GetWindowRect(h, out r);
    int w = r.R - r.L, hh = r.B - r.T;
    if (w <= 0 || hh <= 0 || w > 4000 || hh > 4000) throw new Exception("bad rect " + w + "x" + hh);
    using (var bmp = new Bitmap(w, hh))
    using (var g = Graphics.FromImage(bmp)) {
      g.CopyFromScreen(r.L, r.T, 0, 0, new Size(w, hh));
      bmp.Save(path, ImageFormat.Png);
    }
  }
  [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr p, EnumProc cb, IntPtr l);
  [DllImport("user32.dll")] static extern IntPtr SendMessageText(IntPtr h, uint m, IntPtr w, StringBuilder l);
  [DllImport("user32.dll", EntryPoint = "SendMessageA")] static extern IntPtr SendMessageSB(IntPtr h, uint m, IntPtr w, StringBuilder l);
  [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] static extern bool GetGUIThreadInfo(uint tid, ref GUITHREADINFO gi);
  [StructLayout(LayoutKind.Sequential)] public struct GUITHREADINFO { public int cbSize, flags; public IntPtr hwndActive, hwndFocus, hwndCapture, hwndMenuOwner, hwndMoveSize, hwndCaret; public RECT rcCaret; }
  [DllImport("user32.dll", EntryPoint = "GetWindowLongA")] static extern int GetWindowLongX(IntPtr h, int i);
  public static string StyleOf(IntPtr h) { return string.Format("style=0x{0:x8} exstyle=0x{1:x8}", GetWindowLongX(h, -16), GetWindowLongX(h, -20)); }
  public static string ClassOf(IntPtr h) { var c = new StringBuilder(128); GetClassName(h, c, 128); return c.ToString(); }
  public static string TextOf(IntPtr h) { var s = new StringBuilder(512); SendMessageSB(h, 0x000D, (IntPtr)512, s); return s.ToString(); }
  public static string Focus(uint pid) {
    uint tid = 0;
    foreach (var w in Windows(pid)) { if (w[1].StartsWith("Afx:400000") && w[2] == "Imperialism") { uint p; tid = GetWindowThreadProcessId((IntPtr)long.Parse(w[0]), out p); } }
    var gi = new GUITHREADINFO(); gi.cbSize = Marshal.SizeOf(typeof(GUITHREADINFO));
    GetGUIThreadInfo(tid, ref gi);
    IntPtr fg = GetForegroundWindow();
    return string.Format("foreground={0}({1}) active={2}({3}) focus={4}({5}) capture={6}", fg.ToInt64(), ClassOf(fg), gi.hwndActive.ToInt64(), ClassOf(gi.hwndActive), gi.hwndFocus.ToInt64(), ClassOf(gi.hwndFocus), gi.hwndCapture.ToInt64());
  }
  public static List<string> Children(IntPtr parent) {
    var res = new List<string>();
    EnumChildWindows(parent, (h, l) => {
      RECT r; GetWindowRect(h, out r);
      res.Add(string.Format("{0} {1} vis={2} ({3},{4} {5}x{6}) text='{7}'", h.ToInt64(), ClassOf(h), IsWindowVisible(h), r.L, r.T, r.R - r.L, r.B - r.T, ClassOf(h) == "Edit" ? TextOf(h) : ""));
      return true;
    }, IntPtr.Zero);
    return res;
  }
  public static double DiffImages(string a, string b) {
    using (var x = new Bitmap(a)) using (var y = new Bitmap(b)) {
      int w = Math.Min(x.Width, y.Width), h = Math.Min(x.Height, y.Height); long sum = 0, n = 0;
      for (int i = 0; i < w; i += 8) for (int j = 0; j < h; j += 8) {
        Color p = x.GetPixel(i, j), q = y.GetPixel(i, j);
        sum += Math.Abs(p.R - q.R) + Math.Abs(p.G - q.G) + Math.Abs(p.B - q.B); n++;
      }
      return Math.Round((double)sum / n, 1);
    }
  }
  public static void ShotMargin(IntPtr h, string path, int m) {
    RECT r; GetWindowRect(h, out r);
    int l = Math.Max(0, r.L - m), t = Math.Max(0, r.T - m);
    int w = (r.R - r.L) + 2 * m, hh = (r.B - r.T) + 2 * m;
    using (var bmp = new Bitmap(w, hh))
    using (var g = Graphics.FromImage(bmp)) {
      g.CopyFromScreen(l, t, 0, 0, new Size(w, hh));
      bmp.Save(path, ImageFormat.Png);
    }
  }
  public static string ClientScreenRect(IntPtr h) {
    RECT c; GetClientRect(h, out c); POINT p; p.X = 0; p.Y = 0; ClientToScreen(h, ref p);
    return string.Format("({0},{1} {2}x{3})", p.X, p.Y, c.R, c.B);
  }
  public static void Click(int x, int y) {
    SetCursorPos(x, y); System.Threading.Thread.Sleep(80);
    mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero); System.Threading.Thread.Sleep(60);
    mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
  }
}
'@

function Get-Game { Get-Process Imperialism -ErrorAction SilentlyContinue }
function Show-GameWindows {
  $g = Get-Game; if (-not $g) { 'game not running'; return }
  foreach ($p in $g) { [GW]::Windows([uint32]$p.Id) | ForEach-Object { $_ -join ' | ' } }
}
function Find-Win($cls) {
  $g = Get-Game; if (-not $g) { return [IntPtr]::Zero }
  foreach ($p in $g) { foreach ($w in [GW]::Windows([uint32]$p.Id)) { if ($w[1] -eq $cls -and $w[3] -eq 'vis') { return [IntPtr][int64]$w[0] } } }
  [IntPtr]::Zero
}
function Mirror { Find-Win 'ImperialismMirror' }
