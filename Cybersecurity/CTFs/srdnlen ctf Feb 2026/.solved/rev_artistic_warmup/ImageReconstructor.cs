using System;
using System.IO;
using System.Drawing;
using System.Drawing.Imaging;

class ImageReconstructor {
    static void Main(string[] args) {
        if (args.Length < 3) {
            Console.WriteLine("Usage: ImageReconstructor.exe <input_file> <width> <output_bmp>");
            return;
        }

        string inputFile = args[0];
        int width;
        if (!int.TryParse(args[1], out width)) {
            Console.WriteLine("Invalid width.");
            return;
        }
        string outputFile = args[2];

        try {
            byte[] data = File.ReadAllBytes(inputFile);
            int height = (int)Math.Ceiling((double)data.Length / width);

            using (Bitmap bmp = new Bitmap(width, height, PixelFormat.Format8bppIndexed)) {
                // Set grayscale palette
                ColorPalette cp = bmp.Palette;
                for (int i = 0; i < 256; i++) cp.Entries[i] = Color.FromArgb(i, i, i);
                bmp.Palette = cp;

                BitmapData bmpData = bmp.LockBits(new Rectangle(0, 0, width, height), ImageLockMode.WriteOnly, PixelFormat.Format8bppIndexed);
                
                unsafe {
                    byte* ptr = (byte*)bmpData.Scan0;
                    for (int i = 0; i < data.Length; i++) {
                        ptr[i] = data[i];
                    }
                }

                bmp.UnlockBits(bmpData);
                bmp.Save(outputFile, ImageFormat.Bmp);
            }

            Console.WriteLine(string.Format("Saved {0}x{1} image to {2}", height, width, outputFile));
        } catch (Exception ex) {
            Console.WriteLine("Error: " + ex.Message);
        }
    }
}
