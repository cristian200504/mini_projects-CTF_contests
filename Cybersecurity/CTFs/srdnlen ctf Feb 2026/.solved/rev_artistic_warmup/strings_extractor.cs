using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;

class StringsExtractor {
    static void Main(string[] args) {
        if (args.Length < 1) {
            Console.WriteLine("Usage: strings_extractor.exe <filename>");
            return;
        }

        string filePath = args[0];
        if (!File.Exists(filePath)) {
            Console.WriteLine("File not found: " + filePath);
            return;
        }

        byte[] data = File.ReadAllBytes(filePath);

        Console.WriteLine("--- ASCII Strings ---");
        ExtractStrings(data, Encoding.ASCII);

        Console.WriteLine("\n--- UTF-16 Strings ---");
        ExtractStrings(data, Encoding.Unicode);
    }

    static void ExtractStrings(byte[] data, Encoding encoding) {
        string text = encoding.GetString(data);
        var matches = Regex.Matches(text, @"[ -~]{4,}");
        foreach (Match match in matches) {
            Console.WriteLine(match.Value);
        }
    }
}
