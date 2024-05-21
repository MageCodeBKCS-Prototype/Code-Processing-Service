path="$1"

for file in $path/*.cpp; do
  g++ "$file" -o "${file%.cpp}.out"
done