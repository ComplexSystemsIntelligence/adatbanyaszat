-- pannon-filter.lua
-- 1) PDF-kimenetnél az előre fordított TikZ-ábrák SVG-változata helyett a PDF-et használjuk.
-- 2) A "roadmap", "eset-uzleti" és "eset-mernoki" div-eket PDF-ben tcolorbox-szá alakítjuk.

local function file_exists(path)
  local f = io.open(path, "r")
  if f then f:close() return true end
  return false
end

function Image(img)
  if quarto.doc.is_format("latex") and img.src:match("%.svg$") then
    local pdf = img.src:gsub("%.svg$", ".pdf")
    -- a fejezetek a chapters/ mappában vannak, az útvonal a fájlhoz képest relatív
    local candidates = { pdf, (pdf:gsub("^%.%./", "")) }
    for _, c in ipairs(candidates) do
      if file_exists(c) then img.src = pdf; return img end
    end
    img.src = pdf
    return img
  end
  return img
end

local boxes = {
  ["roadmap"]      = { "peroadmap", "Miről szól a fejezet?" },
  ["eset-uzleti"]  = { "peesetuzleti", "Futó eset · PannonShop" },
  ["eset-mernoki"] = { "peesetmernoki", "Futó eset · Pannon üzem" },
}

function Div(el)
  for cls, spec in pairs(boxes) do
    if el.classes:includes(cls) then
      if quarto.doc.is_format("latex") then
        local out = { pandoc.RawBlock("latex", "\\begin{" .. spec[1] .. "}") }
        for _, b in ipairs(el.content) do table.insert(out, b) end
        table.insert(out, pandoc.RawBlock("latex", "\\end{" .. spec[1] .. "}"))
        return out
      elseif quarto.doc.is_format("epub") then
        local title = pandoc.Para({ pandoc.Strong({ pandoc.Str(spec[2]) }) })
        table.insert(el.content, 1, title)
        return el
      end
    end
  end
  return el
end
