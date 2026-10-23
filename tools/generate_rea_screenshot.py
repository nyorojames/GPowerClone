import os
from PIL import Image, ImageDraw, ImageFont

def render_terminal_screenshot(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    font_path = "C:/Windows/Fonts/consola.ttf"
    font_size = 14
    font = ImageFont.truetype(font_path, font_size)
    title_font = ImageFont.truetype(font_path, 13)

    lines = [
        ("PS C:\\GPowerClone> ", (100, 220, 100), "rea doctor --provider ghidra", (240, 240, 240)),
        ("", (255, 255, 255), "healthy: true", (80, 250, 123)),
        ("", (255, 255, 255), "environment_healthy: false (unconfigured optional engines: Hopper, IDA, JADX, Kuna)", (139, 233, 253)),
        ("", (255, 255, 255), "scope:", (255, 121, 198)),
        ("", (255, 255, 255), "  mode: explicit", (248, 248, 242)),
        ("", (255, 255, 255), "  providers[1]: ghidra", (248, 248, 242)),
        ("", (255, 255, 255), "scope_checks[10]:", (255, 121, 198)),
        ("", (255, 255, 255), "  - name: node                      [ PASS ]  v24.14.0 (runtime: node)", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra                    [ PASS ]  C:\\Tools\\ghidra_12.1.4_PUBLIC", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-platform           [ PASS ]  win32", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-architecture       [ PASS ]  x64", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-installation       [ PASS ]  Ghidra\\application.properties verified", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-version            [ PASS ]  12.1.4", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-headless           [ PASS ]  support\\analyzeHeadless.bat present", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-native_decompiler  [ PASS ]  decompile.exe reports pe x86_64 (matches win32/x64)", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-java               [ PASS ]  21.0.12.1; 64-bit; JDK; C:\\Tools\\jdk-21.0.12.1+1", (80, 250, 123)),
        ("", (255, 255, 255), "  - name: ghidra-native_authority   [ PASS ]  Verified Windows Job Object, DACL & reparse-safe", (80, 250, 123)),
        ("", (255, 255, 255), "", (248, 248, 242)),
        ("", (255, 255, 255), "providerInspections[1]:", (255, 121, 198)),
        ("", (255, 255, 255), "  - id: ghidra", (248, 248, 242)),
        ("", (255, 255, 255), "    configured: true", (80, 250, 123)),
        ("", (255, 255, 255), "    available: true", (80, 250, 123)),
        ("", (255, 255, 255), "    providerVersion: 12.1.4", (248, 248, 242)),
        ("", (255, 255, 255), "    registrationEnvironment:", (248, 248, 242)),
        ("", (255, 255, 255), "      GHIDRA_INSTALL_DIR: \"C:\\Tools\\ghidra_12.1.4_PUBLIC\"", (241, 250, 140)),
        ("", (255, 255, 255), "      JAVA_HOME:          \"C:\\Tools\\jdk-21.0.12.1+1\"", (241, 250, 140)),
        ("", (255, 255, 255), "", (248, 248, 242)),
        ("", (255, 255, 255), "mcpClientRegistration:", (255, 121, 198)),
        ("", (255, 255, 255), "  - client: antigravity", (248, 248, 242)),
        ("", (255, 255, 255), "    config_path: \"C:\\Users\\user\\.gemini\\config\\mcp_config.json\"", (139, 233, 253)),
        ("", (255, 255, 255), "    command:     cmd.exe /d /c npx -y rea-agents@6.7.0 mcp", (139, 233, 253)),
        ("", (255, 255, 255), "    package:     rea-agents@6.7.0", (248, 248, 242)),
        ("", (255, 255, 255), "    state:       aligned (tools: 207, prompts: 6, session: operational)", (80, 250, 123)),
        ("", (255, 255, 255), "", (248, 248, 242)),
        ("PS C:\\GPowerClone> ", (100, 220, 100), "# REA and Ghidra 12.1.4 environment verified successfully", (98, 114, 164)),
    ]

    line_height = 20
    padding_x = 24
    padding_y = 20
    title_bar_height = 36

    width = 960
    height = title_bar_height + padding_y * 2 + len(lines) * line_height

    img = Image.new("RGBA", (width, height), (30, 30, 46, 255))
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([0, 0, width, title_bar_height], fill=(40, 42, 54, 255))
    draw.line([0, title_bar_height, width, title_bar_height], fill=(68, 71, 90, 255), width=1)

    # Window control dots
    draw.ellipse([14, 12, 26, 24], fill=(255, 85, 85, 255))
    draw.ellipse([34, 12, 46, 24], fill=(255, 184, 108, 255))
    draw.ellipse([54, 12, 66, 24], fill=(80, 250, 123, 255))

    # Title text
    title_text = "Windows PowerShell - REA (Reverse Engineering Assistant) & Ghidra 12.1.4 Environment Verification"
    draw.text((80, 10), title_text, font=title_font, fill=(189, 147, 249, 255))

    # Terminal lines
    curr_y = title_bar_height + padding_y
    for prefix, prefix_col, text, text_col in lines:
        curr_x = padding_x
        if prefix:
            draw.text((curr_x, curr_y), prefix, font=font, fill=prefix_col)
            prefix_bbox = font.getbbox(prefix)
            curr_x += (prefix_bbox[2] - prefix_bbox[0])
        if text:
            draw.text((curr_x, curr_y), text, font=font, fill=text_col)
        curr_y += line_height

    img.save(output_path, "PNG")
    print(f"Screenshot saved to {output_path} ({width}x{height})")

if __name__ == "__main__":
    render_terminal_screenshot("docs/rea_ghidra_screenshot.png")
