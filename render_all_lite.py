import glob
import json
import os
import shutil
import traceback
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def load_data():
    """Load all JSON and YAML files from the data/ directory and return a single dictionary."""
    data = {}

    # Load JSON files, handling .json and .JSON file extensions.
    for json_file in glob.glob("data/*.[jJ][sS][oO][nN]"):
        try:
            with open(json_file, "r") as f:
                data.update(json.load(f))
            print(f"Loaded data from {json_file}")
        except Exception as e:
            print(f"Error loading data from {json_file}: {e}")
            traceback.print_exc()

    # Load YAML files, handling .yaml and .YAML extensions.
    for yaml_file in glob.glob("data/*.[yY][aA][mM][lL]"):
        try:
            with open(yaml_file, "r") as f:
                data.update(yaml.safe_load(f))
            print(f"Loaded data from {yaml_file}")
        except Exception as e:
            print(f"Error loading data from {yaml_file}: {e}")
            traceback.print_exc()

    return data

def copy_html_files():
    """Copy .html files from templates/ to site/ without parsing them."""
    if not os.path.exists('site'):
        os.makedirs('site')

    for html_file in glob.glob('templates/**/*.html', recursive=True):
        try:
            destination = os.path.join('site', os.path.relpath(html_file, 'templates'))
            outdir = os.path.dirname(destination)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            if os.path.exists(destination):
                os.remove(destination)
            shutil.copy(html_file, destination)
            print(f'Copied {html_file} to {destination}')
        except Exception as e:
            print(f'Error copying {html_file} to {destination}: {e}')
            traceback.print_exc()

def render_all_templates(env, data, trigger_file=None):
    """Render all templates, excluding partials."""

    if trigger_file:
        if isinstance(trigger_file, list):
            trigger_file = trigger_file[0]
        print(f'>>> Rebuild triggered by change in: {trigger_file}')
        if trigger_file.endswith('.html'):
            copy_html_files()
            return

    if not os.path.exists('site'):
        os.makedirs('site')

    # Collect templates from templates/ directory, excluding partials
    template_files = [f for f in glob.glob('templates/**/*.*', recursive=True) if f.endswith(('.j2', '.jinja')) and 'partials' not in f]

    for template_path in template_files:
        try:
            template = env.get_template(os.path.relpath(template_path, 'templates'))
            output = template.render(data)
            outname = os.path.join('site', os.path.relpath(template_path, 'templates').replace('.html.j2', '.html').replace('.j2', '.html').replace('.html.jinja', '.html').replace('.jinja', '.html'))
            outdir = os.path.dirname(outname)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            with open(outname, 'w') as out:
                out.write(output)
            print(f'Rendered {template_path} to {outname}')
        except TemplateError as e:
            print(f'Error rendering {template_path}: {e}')
            traceback.print_exc()
        except Exception as e:
            print(f'Unexpected error rendering {template_path}: {e}')
            traceback.print_exc()

def render_all(trigger_file=None):
    print(f'Calling render_all with trigger_file: {trigger_file}')
    env = Environment(loader=FileSystemLoader('templates'))
    data = load_data()
    render_all_templates(env, data, trigger_file)

class ChangeHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print(f'Modified: {event.src_path}')
        if not event.is_directory and (event.src_path.startswith('templates/') or event.src_path.startswith('data/')):
            render_all(event.src_path)

    def on_created(self, event):
        print(f'Created: {event.src_path}')
        if not event.is_directory and (event.src_path.startswith('templates/') or event.src_path.startswith('data/')):
            render_all(event.src_path)

    def on_deleted(self, event):
        print(f'Deleted: {event.src_path}')
        if not event.is_directory and (event.src_path.startswith('templates/') or event.src_path.startswith('data/')):
            render_all(event.src_path)

if __name__ == "__main__":
    render_all()

    event_handler = ChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, 'templates/', recursive=True)
    observer.schedule(event_handler, 'data/', recursive=True)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()