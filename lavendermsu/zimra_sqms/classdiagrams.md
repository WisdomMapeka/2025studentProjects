Generate Class Diagram

Run this in your project root (where manage.py lives):

pyreverse -o png -p rise_diagram .


-o png → output image format

-p rise_diagram → project name (prefix for files)

. → current directory

This generates:

classes_rise_diagram.png
packages_rise_diagram.png


✅ classes_rise_diagram.png → Class Diagram
✅ packages_rise_diagram.png → Package Diagram

3️⃣ Generate for a specific app only

Example for your policies app:

pyreverse -o png -p policies_diagram policies/


Output:

classes_policies_diagram.png
packages_policies_diagram.png

4️⃣ (Optional) Generate SVG (for zoomable diagrams)
pyreverse -o svg -p loanmanager_diagram loanmanager/


Now you can embed it in docs or open it in the browser.

### Gnerating many for each app

# Create output folder
mkdir classdiagrams -ErrorAction SilentlyContinue

# List all app folders (those with models.py)
$apps = Get-ChildItem -Directory | Where-Object { Test-Path "$($_.FullName)\models.py" }

foreach ($app in $apps) {
    $name = $app.Name
    Write-Host "📦 Generating UML Class Diagram for $name..."

    # Run pyreverse on this app
    pyreverse -o png -p ${name}_diagram "$($app.FullName)"

    # Move generated PNGs into classdiagrams folder
    if (Test-Path "classes_${name}_diagram.png") {
        Move-Item "classes_${name}_diagram.png" "classdiagrams\classes_${name}_diagram.png" -Force
    }
    if (Test-Path "packages_${name}_diagram.png") {
        Move-Item "packages_${name}_diagram.png" "classdiagrams\packages_${name}_diagram.png" -Force
    }

    Write-Host "✅ Saved → classdiagrams\classes_${name}_diagram.png"
}
Write-Host "`n🎉 All class diagrams generated and saved in /classdiagrams/"
