﻿// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using System.Text;
using System.IO;
using System.Linq;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Drawing;
using Graphics = System.Drawing.Graphics;
using System.Drawing.Imaging;
using WindowsInput; 
using WindowsInput.Native;

public class ExternalWindowManager : MonoBehaviour
{
    // private const int scoreWidth = 135;
    // private const int scoreHeight = 22;
    // private const int scoreYOffset = 243;
    // private const int scoreXOffset = 436;
    // private const int numberHeight = 22;
    // private const int numberWidth = 15;
    // private const int ballYOffset = 198;
    // private const int ballXOffset = 556;

    private const int scoreWidth = 104;
    private const int scoreHeight = 20;
    private const int scoreYOffset = 4;
    private const int scoreXOffset = 160;
    private const int numberHeight = 18;
    private const int numberWidth = 13;
    private const int ballYOffset = 45;
    private const int ballXOffset = 251;

    public static long Score => score;
    public static int Ball => ball;

    private static long score;
    private static int ball;

    public static int frame = 0; 

    // public string FilePath = @"C:\Program Files (x86)\Microsoft Games\Pinball\pinball.exe";
    // public string WorkingDirectory = @"C:\Program Files (x86)\Microsoft Games\Pinball";
    // public string WindowTitle = "3D Pinball for Windows - Space Cadet";
    public string FilePath = @"C:\Visual Pinball\VPinballX.exe";
    public string WorkingDirectory = @"C:\Visual Pinball";
    public string WindowTitle = "Visual Pinball Player";
    public RenderTexture renderTexture;

    private Process proc;
    private User32.Rect rect;

    // When first enabled ensure the software will run in background
    void Awake()
    {
        if (Application.isEditor)
            Application.runInBackground = true;
    }

    // To read from txt file
    string ReadFile(string filePath)
    {
             
        // Read the entire file content
        string content = File.ReadAllText(filePath);
        
        return content; 
    }

    // Start is called before the first frame update
    void Start()
    {
        rect = new User32.Rect();
        proc = Process.GetProcesses().Where(x => x.ProcessName.Contains("VPinballX")).FirstOrDefault();
        Process[] processes = Process.GetProcesses();
        
        if (proc == null)
        {
            UnityEngine.Debug.Log("Entered process loop"); 
            proc = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = FilePath,
                    WorkingDirectory = WorkingDirectory,
                    UseShellExecute = false,
                    RedirectStandardOutput = false,
                    CreateNoWindow = true,
                    WindowStyle = ProcessWindowStyle.Normal,
                },
            };
            proc.Start();
        }
        User32.UnityWindow = User32.GetActiveWindow();

    }



    // Update is called once per frame
    void Update()
    {
        StartCoroutine(CaptureWindow());
    }

    /// <summary>
    /// Capture the pixels from an external window and detect the numbers present
    /// </summary>
    /// <returns></returns>
    private IEnumerator CaptureWindow()
    {
        // Look for the external program by its title and get the window handle
        User32.GetWindowByTitle(WindowTitle, ref rect);

        // Dont capture frame until the window is in focus
        yield return new WaitWhile(() => User32.UnityWindow == User32.GetActiveWindow());

        int width = rect.right - rect.left;
        int height = rect.bottom - rect.top;
        if (width == 0 || height == 0)
        {
            UnityEngine.Debug.Log("Window found but size 0,0");
            yield return new WaitForSeconds(1);
        }
        else
        {
            //Uncomment for debug
            // UnityEngine.Debug.Log($"Found Window {width},{height}");
        }

        // Create Images in memory
        Bitmap bmp = new Bitmap(width, height);
        Bitmap current = new Bitmap(scoreWidth, scoreHeight);
        Bitmap last = new Bitmap(scoreWidth, scoreHeight);
        Bitmap number = new Bitmap(numberWidth, numberHeight);
        Graphics graphics = Graphics.FromImage(bmp);
        Graphics cg = Graphics.FromImage(current);
        Graphics lg = Graphics.FromImage(last);
        Graphics ng = Graphics.FromImage(number);


        //Copy from screen into image
        graphics.CopyFromScreen(rect.left, rect.top, 0, 0, new Size(bmp.Width, bmp.Height), CopyPixelOperation.SourceCopy); //ARGB32
        using (MemoryStream ms = new MemoryStream())
        {
            bmp.Save(ms, System.Drawing.Imaging.ImageFormat.Png);

            // //Uncomment - If you weant to save frames to disk
            // bmp.Save("C:/Users/richa/OneDrive/Desktop/frames/" + frame + ".bmp", System.Drawing.Imaging.ImageFormat.Bmp);
            // frame++;

            var buffer = new byte[ms.Length];
            ms.Position = 0;
            ms.Read(buffer, 0, buffer.Length);

            var Height = 116;
            var Width = 152;

            Texture2D texture = new Texture2D(Width, Height, TextureFormat.R8, false, false);
            texture.LoadImage(buffer);
            texture.Apply();

            UnityEngine.Graphics.Blit(texture, renderTexture);
            UnityEngine.Object.Destroy(texture);
        }

        // Get scoreboard numbers
        Size scoreSize = new Size(scoreWidth, scoreHeight);
        cg.DrawImage(bmp,
            new Rectangle(new Point(0, 0), scoreSize),
            new Rectangle(new Point(scoreXOffset, scoreYOffset), scoreSize),
            GraphicsUnit.Pixel);

        try{
            score = Int32.Parse(ReadFile(@"C:\Users\Pinbot\Desktop\data\score.txt")); 
        }
        catch{
            UnityEngine.Debug.Log("Could not read score");
        }
        try {
            ball = Int32.Parse(ReadFile(@"C:\Users\Pinbot\Desktop\data\ballcount.txt"));
        }
        catch{
            UnityEngine.Debug.Log("Could not read ball");
        }

        //Uncomment for debug
        UnityEngine.Debug.Log("Ball " + ball + ", Score " + score);

        lg.DrawImage(current, new Point(0, 0));

        ng.Dispose();
        lg.Dispose();
        cg.Dispose();
        graphics.Dispose();
        number.Dispose();
        last.Dispose();
        current.Dispose();
        bmp.Dispose();
      
        GC.Collect();
        GC.WaitForPendingFinalizers();
        yield return new WaitForSeconds(1);
    }



    // [DllImport ("User32.dll")]
    // static extern int SetForegroundWindow(IntPtr point);

    // public void TypeKey(char c)
    // {
    //     // Process p = Process.GetProcessesByName("").FirstOrDefault();
    //     if (proc != null)
    //     {
    //         IntPtr h = proc.MainWindowHandle;
    //         SetForegroundWindow(h);
    //         System.Windows.Forms.SendKeys.SendWait("z");
    //     }
    // }

    /// <summary>
    /// Compare images to see if pixels match
    /// </summary>
    /// <param name="a">Image 1</param>
    /// <param name="b">Image 2</param>
    /// <returns></returns>
    static bool Compare(Bitmap a, Bitmap b)
    {
        for (int x = 0; x < a.Width; x++)
            for (int y = 0; y < a.Height; y++)
            {
                if (a.GetPixel(x, y) != b.GetPixel(x, y))
                {
                    return false;
                }
            }
        return true;
    }

    /// <summary>
    /// A Windows User32.dll (external) wrapper class - InteropServices
    /// </summary>
    private class User32
    {
        [StructLayout(LayoutKind.Sequential)]
        public struct Rect
        {
            public int left;
            public int top;

            public int right;
            public int bottom;
        }
        #region Keys
        //bVirtualKey
        //Virtual keycode that has to be send as key input.The following are the available predefined virtual key codes:
        //VK_NUMPAD7	0x67	VK_BACK	0x08
        //VK_NUMPAD8	0x68	VK_TAB	0x09
        //VK_NUMPAD9	0x69	VK_RETURN	0x0D
        //VK_MULTIPLY	0x6A	VK_SHIFT	0x10
        //VK_ADD	0x6B	    VK_CONTROL	0x11
        //VK_SEPARATOR	0x6C	VK_MENU	0x12
        //VK_SUBTRACT	0x6D	VK_PAUSE	0x13
        //VK_DECIMAL	0x6E	VK_CAPITAL	0x14
        //VK_DIVIDE	0x6F	    VK_ESCAPE	0x1B
        //VK_F1	0x70	        VK_SPACE	0x20
        //VK_F2	0x71	        VK_END	0x23
        //VK_F3	0x72	        VK_HOME	0x24
        //VK_F4	0x73	        VK_LEFT	0x25
        //VK_F5	0x74	        VK_UP	0x26
        //VK_F6	0x75	        VK_RIGHT	0x27
        //VK_F7	0x76	        VK_DOWN	0x28
        //VK_F8	0x77	        VK_PRINT	0x2A
        //VK_F9	0x78	        VK_SNAPSHOT	0x2C
        //VK_F10	0x79	    VK_INSERT	0x2D
        //VK_F11	0x7A	    VK_DELETE	0x2E
        //VK_F12	0x7B	    VK_LWIN	0x5B
        //VK_NUMLOCK 0x90	    VK_RWIN	0x5C
        //VK_SCROLL	0x91	    VK_NUMPAD0	0x60
        //VK_LSHIFT	0xA0	    VK_NUMPAD1	0x61
        //VK_RSHIFT	0xA1	    VK_NUMPAD2	0x62
        //VK_LCONTROL 0xA2	    VK_NUMPAD3	0x63
        //VK_RCONTROL 0xA3	    VK_NUMPAD4	0x64
        //VK_LMENU	0xA4	    VK_NUMPAD5	0x65
        //VK_RMENU	0xA5	    VK_NUMPAD6	0x66

        const int VK_F2 = 0x71;
        const int ALT = 0xA4;
        const int SPACE = 0x20;
        const int EXTENDEDKEY = 0x1;
        const int KEYUP = 0x2;
        #endregion

        /// <summary>
        /// Press a key down virtually
        /// </summary>
        /// <param name="key"></param>
        public static void KeyDown(int key)
        {
            switch (key)
            {
                case SPACE:
                    keybd_event((byte)SPACE, 0x45, EXTENDEDKEY | 0, 0);
                    break;
                default:
                    keybd_event((byte)key, 0x9e, 0, 0);
                    break;
            }

        }
        public static void KeyDown(char key)
        {
            keybd_event((byte)VkKeyScan(key), 0x9e, 0, 0);
        }

        /// <summary>
        /// Stop pressing a key virtually
        /// </summary>
        /// <param name="key"></param>
        public static void KeyUp(int key)
        {
            switch (key)
            {
                case SPACE:
                    keybd_event((byte)SPACE, 0x45, EXTENDEDKEY | KEYUP, 0);
                    break;
                default:
                    keybd_event((byte)key, 0x9e, KEYUP, 0);
                    break;
            }

        }
        public static void KeyUp(char key)
        {
            keybd_event((byte)VkKeyScan(key), 0x9e, KEYUP, 0);
        }


        public static IntPtr UnityWindow;
        public static IntPtr corehWnd;
        private const int MAXTITLE = 255;
        private static string windowTitle;

        /// <summary>
        /// Finds and get the window handle for the external process. Matching by Window Title.
        /// </summary>
        /// <param name="windowTitle"></param>
        /// <param name="rect"></param>
        /// <returns></returns>
        public static bool GetWindowByTitle(string windowTitle, ref Rect rect)
        {
            User32.windowTitle = windowTitle;
            if (corehWnd == IntPtr.Zero)
            {
                _EnumDesktopWindows(IntPtr.Zero, new EnumDelegate(User32.EnumWindowsProc), IntPtr.Zero);
            }
            // Check corehWnd anfter enumeration
            if (corehWnd != IntPtr.Zero)
            {
                GetWindowRect(corehWnd, ref rect);
                return true;
            }
            return false;
        }

        /// <summary>
        /// Enum Windows Callback
        /// </summary>
        /// <param name="hWnd"></param>
        /// <param name="lParam"></param>
        /// <returns></returns>
        private static bool EnumWindowsProc(IntPtr hWnd, int lParam)
        {
            StringBuilder title = new StringBuilder(MAXTITLE);
            int titleLength = _GetWindowText(hWnd, title, title.Capacity + 1);
            title.Length = titleLength;
            if (title.ToString() == User32.windowTitle)
            {
                corehWnd = hWnd;
            }
            return true;
        }

        /// <summary>
        /// Callback funtion delegate
        /// </summary>
        /// <param name="hWnd"></param>
        /// <param name="lParam"></param>
        /// <returns></returns>
        private delegate bool EnumDelegate(IntPtr hWnd, int lParam);
        [DllImport("user32.dll", EntryPoint = "GetWindowText", ExactSpelling = false, CharSet = CharSet.Auto, SetLastError = true)]
        private static extern int _GetWindowText(IntPtr hWnd, StringBuilder lpWindowText, int nMaxCount);
        [DllImport("user32.dll", EntryPoint = "EnumDesktopWindows", ExactSpelling = false, CharSet = CharSet.Auto, SetLastError = true)]
        private static extern bool _EnumDesktopWindows(IntPtr hDesktop, EnumDelegate lpEnumCallbackFunction, IntPtr lParam);
        [DllImport("user32.dll")]
        public static extern IntPtr GetWindowRect(IntPtr hWnd, ref Rect rect);
        [DllImport("user32.dll")]
        public static extern IntPtr GetActiveWindow();
        [DllImport("user32.dll")]
        private static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, int dwExtraInfo);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        private static extern short VkKeyScan(char ch);
    }
}
