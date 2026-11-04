-- latex-macros-to-unicode.lua
--
-- DOCX and PPTX have no LaTeX engine, so two constructs the PDF path depends on
-- are silently lost there:
--   * `\ce{...}` (mhchem) survives only as literal text "$\ce{Mg^2+}$";
--   * `\qty{}{}` (siunitx) is a RawInline that Pandoc's DOCX writer DROPS whole,
--     so the quantity vanishes with no warning.
--
-- This filter rewrites both into Unicode so the non-LaTeX formats match the PDF.
-- Apply it ONLY to docx/pptx. The PDF path must keep the real LaTeX macros.
--
-- SCOPE: covers charges, subscripts, simple formulae, and the unit macros listed
-- in MACRO below. It does NOT cover full mhchem (reactions with conditions,
-- isotopes beyond the simple forms, state symbols, electron configurations).
-- For those, hand-write the Unicode in a DOCX-bound document.

local SUP = {
  ['0'] = '⁰', ['1'] = '¹', ['2'] = '²', ['3'] = '³', ['4'] = '⁴',
  ['5'] = '⁵', ['6'] = '⁶', ['7'] = '⁷', ['8'] = '⁸', ['9'] = '⁹',
  ['+'] = '⁺', ['-'] = '⁻',
}
local SUB = {
  ['0'] = '₀', ['1'] = '₁', ['2'] = '₂', ['3'] = '₃', ['4'] = '₄',
  ['5'] = '₅', ['6'] = '₆', ['7'] = '₇', ['8'] = '₈', ['9'] = '₉',
  ['+'] = '₊', ['-'] = '₋',
}

local function map_chars(s, tbl)
  return (s:gsub('.', function(c) return tbl[c] or c end))
end

-- Unit macros: prefix and unit names, mirroring siunitx spellings.
local MACRO = {
  ['milli'] = 'm', ['micro'] = 'µ', ['nano'] = 'n', ['pico'] = 'p',
  ['kilo'] = 'k', ['centi'] = 'c', ['deci'] = 'd', ['femto'] = 'f',
  ['mole'] = 'mol', ['litre'] = 'L', ['liter'] = 'L',
  ['gram'] = 'g', ['metre'] = 'm', ['meter'] = 'm',
  ['second'] = 's', ['minute'] = 'min', ['hour'] = 'h',
  ['degreeCelsius'] = '°C', ['celsius'] = '°C', ['kelvin'] = 'K',
  ['ampere'] = 'A', ['volt'] = 'V', ['watt'] = 'W', ['joule'] = 'J',
  ['newton'] = 'N', ['pascal'] = 'Pa', ['bar'] = 'bar', ['molar'] = 'M',
  ['per'] = '/', ['of'] = '',
}

local function expand_macros(s)
  return (s:gsub('\\(%a+)', function(name) return MACRO[name] or ('\\' .. name) end))
end

-- Renders a siunitx unit spec. `\per` becomes a reciprocal, matching the
-- "mmol L⁻¹" form siunitx produces on the PDF side.
local function expand_unit(unit)
  if not unit:match('\\') then
    return unit  -- already a literal string such as "mmol/L"
  end
  local num, den = unit:match('^(.-)\\per(.*)$')
  if num then
    return expand_macros(num) .. ' ' .. expand_macros(den) .. '⁻¹'
  end
  return expand_macros(unit)
end

local ARROWS = {
  ['<=>'] = '⇌', ['<->'] = '↔', ['->'] = '→', ['<-'] = '←',
}

local function chem_to_unicode(body)
  for tex, uni in pairs(ARROWS) do
    body = body:gsub(tex:gsub('%p', '%%%0'), uni)
  end

  local out = {}
  local i, n = 1, #body
  local sub_run = false
  while i <= n do
    local c = body:sub(i, i)
    if c == '^' or c == '_' then
      local j = i + 1
      local arg
      if body:sub(j, j) == '{' then
        local depth, k = 1, j + 1
        while k <= n and depth > 0 do
          local ch = body:sub(k, k)
          if ch == '{' then depth = depth + 1
          elseif ch == '}' then depth = depth - 1 end
          k = k + 1
        end
        arg = body:sub(j + 1, k - 2)
        i = k
      else
        local k = j
        while k <= n and body:sub(k, k):match('[%d%+%-]') do k = k + 1 end
        arg = body:sub(j, k - 1)
        i = k
      end
      out[#out + 1] = (c == '^') and map_chars(arg, SUP) or map_chars(arg, SUB)
      sub_run = (c == '_')
    elseif c:match('%d') then
      -- mhchem auto-subscripts digits after an element symbol, and keeps
      -- going while the digits continue (C6H12O6 -> C₆H₁₂O₆, not C₆H₁2O₆).
      local prev = out[#out]
      if sub_run or (prev and prev:match('[%a%)%]]$')) then
        out[#out + 1] = map_chars(c, SUB)
        sub_run = true
      else
        out[#out + 1] = c
        sub_run = false
      end
      i = i + 1
    else
      out[#out + 1] = c
      sub_run = false
      i = i + 1
    end
  end
  return table.concat(out)
end

function Math(el)
  local ce = el.text:match('^%s*\\ce{(.*)}%s*$')
  if ce then
    return pandoc.Str(chem_to_unicode(ce))
  end
  -- Authors sometimes wrap \qty inside $...$ by habit; handle both spellings.
  local num, unit = el.text:match('^%s*\\qty{(.-)}{(.-)}%s*$')
  if num and unit then
    return pandoc.Str(num .. ' ' .. expand_unit(unit))
  end
end

function RawInline(el)
  if el.format ~= 'tex' and el.format ~= 'latex' then
    return nil
  end
  local num, unit = el.text:match('^\\qty{(.-)}{(.-)}$')
  if not num then
    num, unit = el.text:match('^\\SI{(.-)}{(.-)}$')
  end
  if num and unit then
    return pandoc.Str(num .. ' ' .. expand_unit(unit))
  end
  local unit_only = el.text:match('^\\unit{(.-)}$')
  if unit_only then
    return pandoc.Str(expand_unit(unit_only))
  end
end
