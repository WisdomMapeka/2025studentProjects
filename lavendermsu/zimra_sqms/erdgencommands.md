Generate a diagram for all apps:
python manage.py graph_models -a -o erd.dot


OR only for one app (e.g. insurance):

python manage.py graph_models insurance -o insurance_erd.dot


Now convert the .dot file into an image:

dot -Tpng erd.dot -o erd.png
# OR (better quality)
dot -Tsvg erd.dot -o erd.sv


🧩 Step 5 — (Optional) Make it prettier

You can add flags for better visuals:

python manage.py graph_models -a -g -o erd.dot


-a → all apps

-g → group models by app

-o → output file

Then render again:

dot -Tpng erd.dot -o erd.png


### Generation ERD for many apps
If using PowerShell (recommended on Windows):

Run this inside your Django project root:


mkdir diagrams
$apps = python manage.py showmigrations | Select-String -Pattern "^\w" | ForEach-Object { ($_ -split ' ')[0] } | Sort-Object -Unique
foreach ($app in $apps) {
    Write-Host "Generating ERD for $app..."
    python manage.py graph_models $app -g -o "diagrams\$app.dot"
    dot -Tpng "diagrams\$app.dot" -o "diagrams\$app.png"
}
Write-Host "✅ Done! ERDs saved in /diagrams/"
