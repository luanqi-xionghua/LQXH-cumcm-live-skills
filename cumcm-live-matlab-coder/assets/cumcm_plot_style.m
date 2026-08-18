function style = cumcm_plot_style(fig, ax, fontName, paletteSet)
%CUMCM_PLOT_STYLE Apply one explicitly selected CUMCM paper palette.
%   STYLE = CUMCM_PLOT_STYLE(FIG, AX, FONTNAME, PALETTESET) changes
%   presentation only. PALETTESET must be SET-A, SET-B, SET-C, or SET-D.
%   FONTNAME must be an installed font verified on the current machine.

if nargin < 1 || isempty(fig)
    fig = gcf;
end
if nargin < 2 || isempty(ax)
    ax = findall(fig, "Type", "axes");
end
if nargin < 3 || isempty(fontName)
    fontName = get(groot, "FactoryAxesFontName");
end
if nargin < 4 || isempty(paletteSet)
    error("cumcm_plot_style:PaletteRequired", ...
        "palette_set is required; explicitly choose SET-A, SET-B, SET-C, or SET-D");
end

paletteSet = upper(strtrim(string(paletteSet)));
switch paletteSet
    case "SET-A"
        style.colors = [ ...
            43 73 93;    ... % primary #2B495D
            179 161 75;  ... % contrast #B3A14B
            208 186 220; ... % auxiliary #D0BADC
            129 129 129; ... % neutral #818181
            182 48 59     ... % accent #B6303B
            ] / 255;
        style.paletteBasis = "深海蓝主色—红色重点—金黄对比—淡紫辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.59–78.28，相邻最小 ΔL*=12.09";
    case "SET-B"
        style.colors = [ ...
            105 46 111;  ... % primary #692E6F
            83 180 116;  ... % contrast #53B474
            215 188 183; ... % auxiliary #D7BCB7
            129 129 129; ... % neutral #818181
            76 108 32     ... % accent #4C6C20
            ] / 255;
        style.paletteBasis = "深茄紫主色—黄绿重点—绿色对比—淡橙红辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.68–78.36，相邻最小 ΔL*=12.04";
    case "SET-C"
        style.colors = [ ...
            92 64 43;    ... % primary #5C402B
            147 158 215; ... % contrast #939ED7
            175 202 162; ... % auxiliary #AFCAA2
            129 129 129; ... % neutral #818181
            30 110 103    ... % accent #1E6E67
            ] / 255;
        style.paletteBasis = "深橙棕主色—青色重点—蓝紫对比—淡绿辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.71–78.44，相邻最小 ΔL*=12.12";
    case "SET-D"
        style.colors = [ ...
            42 78 38;    ... % primary #2A4E26
            211 138 186; ... % contrast #D38ABA
            167 200 207; ... % auxiliary #A7C8CF
            129 129 129; ... % neutral #818181
            123 65 205    ... % accent #7B41CD
            ] / 255;
        style.paletteBasis = "深墨绿主色—靛紫重点—品红对比—淡青蓝辅助；与其他组同角色色相距均≥88.2°，CIELAB L*≈29.62–78.48，相邻最小 ΔL*=12.13";
    otherwise
        error("cumcm_plot_style:UnknownPalette", ...
            "Unknown palette_set %s; choose SET-A, SET-B, SET-C, or SET-D", paletteSet);
end

style.paletteSet = paletteSet;
style.light = [245 245 242] / 255;
style.sequential = interp1( ...
    linspace(0, 1, 6), ...
    [style.light; style.colors(3,:); style.colors(2,:); ...
     style.colors(4,:); style.colors(5,:); style.colors(1,:)], ...
    linspace(0, 1, 256));
style.diverging = interp1( ...
    linspace(0, 1, 5), ...
    [style.colors(1,:); [220 228 232] / 255; style.light; ...
     [232 218 215] / 255; style.colors(5,:)], ...
    linspace(0, 1, 256));
style.fontName = fontName;
style.lineWidth = 1.5;
style.markerSize = 5;
textColor = [79 85 90] / 255;

if exist("theme", "file") == 2
    try
        theme(fig, "light");
    catch
        % Older releases do not expose per-figure themes.
    end
end

set(fig, ...
    "Color", "w", ...
    "Renderer", "painters", ...
    "DefaultTextColor", textColor);

for k = 1:numel(ax)
    current = ax(k);
    colororder(current, style.colors);
    set(current, ...
        "FontName", fontName, ...
        "FontSize", 9, ...
        "LineWidth", 0.8, ...
        "Color", "w", ...
        "XColor", textColor, ...
        "YColor", textColor, ...
        "Box", "off", ...
        "TickDir", "out", ...
        "XGrid", "on", ...
        "YGrid", "on", ...
        "GridColor", [209 213 219] / 255, ...
        "GridAlpha", 0.65, ...
        "Layer", "top");
end

legends = findall(fig, "Type", "legend");
if ~isempty(legends)
    set(legends, ...
        "Color", "w", ...
        "TextColor", textColor, ...
        "EdgeColor", [209 213 219] / 255);
end
end
