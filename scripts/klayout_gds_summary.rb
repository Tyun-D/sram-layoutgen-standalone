input = $input
output = $output
top_name = $topcell

raise "missing -rd input=..." unless input
raise "missing -rd output=..." unless output

layout = RBA::Layout::new
layout.read(input)
top = top_name && top_name.length > 0 ? layout.cell(top_name) : layout.top_cell
top = layout.top_cell unless top
raise "no top cell found in #{input}" unless top

bbox = top.bbox
dbu = layout.dbu
refs = Hash.new(0)
top.each_inst do |inst|
  refs[inst.cell.name] += 1
end

File.open(output, "w") do |f|
  f.puts "{"
  f.puts "  \"input\": \"#{input.gsub("\\", "\\\\\\\\")}\","
  f.puts "  \"topcell\": \"#{top.name}\","
  f.puts "  \"dbu_um\": #{dbu},"
  f.puts "  \"bbox_um\": {"
  f.puts "    \"x0\": #{bbox.left * dbu},"
  f.puts "    \"y0\": #{bbox.bottom * dbu},"
  f.puts "    \"x1\": #{bbox.right * dbu},"
  f.puts "    \"y1\": #{bbox.top * dbu},"
  f.puts "    \"width\": #{bbox.width * dbu},"
  f.puts "    \"height\": #{bbox.height * dbu}"
  f.puts "  },"
  f.puts "  \"cell_count\": #{layout.cells},"
  f.puts "  \"top_ref_count\": #{top.each_inst.to_a.length},"
  f.puts "  \"top_refs\": {"
  refs.keys.sort.each_with_index do |name, idx|
    comma = idx == refs.keys.length - 1 ? "" : ","
    f.puts "    \"#{name}\": #{refs[name]}#{comma}"
  end
  f.puts "  }"
  f.puts "}"
end
