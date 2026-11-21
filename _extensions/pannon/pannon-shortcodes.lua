-- pannon-shortcodes.lua
-- {{< app kmeans height=560 title="..." >}}  – interaktív HTML-alkalmazás beágyazása
-- {{< colab 05-csoportositas-ertsd-meg >}}     – "Megnyitás Colabban" hivatkozás
-- {{< notebook 05-csoportositas-ertsd-meg >}} – Colab + GitHub hivatkozás együtt

local function meta_str(meta, key, default)
  local v = meta[key]
  if v == nil then return default end
  return pandoc.utils.stringify(v)
end

local function kw(kwargs, key, default)
  local v = kwargs[key]
  if v == nil then return default end
  local s = pandoc.utils.stringify(v)
  if s == "" then return default end
  return s
end

local function colab_url(meta, nb)
  local repo = meta_str(meta, "book-repo", "ComplexSystemsIntelligence/adatbanyaszat")
  local branch = meta_str(meta, "book-branch", "main")
  return "https://colab.research.google.com/github/" .. repo .. "/blob/" .. branch ..
         "/notebooks/" .. nb .. ".ipynb"
end

local function github_url(meta, path)
  local repo = meta_str(meta, "book-repo", "ComplexSystemsIntelligence/adatbanyaszat")
  local branch = meta_str(meta, "book-branch", "main")
  return "https://github.com/" .. repo .. "/blob/" .. branch .. "/" .. path
end

return {
  ["app"] = function(args, kwargs, meta)
    local name = pandoc.utils.stringify(args[1])
    local height = kw(kwargs, "height", "560")
    local title = kw(kwargs, "title", "Interaktív alkalmazás")
    local site = meta_str(meta, "book-site", "https://complexsystemsintelligence.github.io/adatbanyaszat/")
    local abs = site .. "apps/" .. name .. ".html"
    if quarto.doc.is_format("html") and not quarto.doc.is_format("epub") then
      local html = '<div class="pe-app"><div class="pe-app-bar"><span>' .. title ..
        '</span><a href="../apps/' .. name .. '.html" target="_blank" rel="noopener">Megnyitás új lapon ↗</a></div>' ..
        '<iframe src="../apps/' .. name .. '.html" style="height:' .. height ..
        'px" loading="lazy" title="' .. title .. '"></iframe></div>'
      return pandoc.RawBlock("html", html)
    else
      return pandoc.Div({
        pandoc.Para({ pandoc.Strong({ pandoc.Str("Interaktív alkalmazás: ") }), pandoc.Str(title) }),
        pandoc.Para({ pandoc.Str("A böngészőben futtatható változat: "), pandoc.Link(abs, abs) })
      }, pandoc.Attr("", { "callout-tip" }))
    end
  end,

  ["colab"] = function(args, kwargs, meta)
    local nb = pandoc.utils.stringify(args[1])
    local url = colab_url(meta, nb)
    return pandoc.Link({ pandoc.Str("Megnyitás Colabban: " .. nb) }, url)
  end,

  ["notebook"] = function(args, kwargs, meta)
    local nb = pandoc.utils.stringify(args[1])
    local label = kw(kwargs, "label", nb)
    local curl = colab_url(meta, nb)
    local gurl = github_url(meta, "notebooks/" .. nb .. ".ipynb")
    if quarto.doc.is_format("html") and not quarto.doc.is_format("epub") then
      local html = '<div class="pe-badges"><a href="' .. curl .. '" target="_blank" rel="noopener">▶ Colab: ' ..
        label .. '</a><a href="' .. gurl .. '" target="_blank" rel="noopener">GitHub forrás</a></div>'
      return pandoc.RawBlock("html", html)
    else
      return pandoc.Para({ pandoc.Strong({ pandoc.Str("Colab-notebook: ") }), pandoc.Link(label, curl) })
    end
  end,
}
