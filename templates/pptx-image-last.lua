-- For pptx output, move standalone images to the end of each slide.
--
-- Pandoc's pptx writer only uses the side-by-side "Content with Caption"
-- layout when text comes before the image; an image *before* text gets
-- stacked in the same placeholder as the text and overlaps it. Many
-- slides in these lectures put the image first (fine in reveal.js), so
-- reorder them here rather than in the source markdown.

local SLIDE_LEVEL = 2 -- keep in sync with --slide-level in the Makefile

local function is_standalone_image(block)
	if block.t == 'Figure' then
		return true
	end
	return (block.t == 'Para' or block.t == 'Plain')
		and #block.content == 1
		and block.content[1].t == 'Image'
end

function Pandoc(doc)
	if not FORMAT:match('pptx') then
		return doc
	end
	local out = pandoc.List()
	local text = pandoc.List()
	local images = pandoc.List()
	local function flush()
		out:extend(text)
		out:extend(images)
		text, images = pandoc.List(), pandoc.List()
	end
	for _, block in ipairs(doc.blocks) do
		if block.t == 'Header' and block.level <= SLIDE_LEVEL then
			flush()
			out:insert(block)
		elseif is_standalone_image(block) then
			images:insert(block)
		else
			text:insert(block)
		end
	end
	flush()
	doc.blocks = out
	return doc
end
