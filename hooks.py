import sublime
import sublime_plugin

from pathlib import Path


class HooksListener(sublime_plugin.EventListener):
    def get_hooks(self, view, namespace):
        # Retrieve the current settings
        view_settings = view.settings()

        # Collect all levels of cmds into a list
        # DEV: Occasionally, ST3 recognizes settings set to `None` causing errors like #1
        # DEV: As a result, we fallback outside of the `dict` lookup
        cmds = []
        cmds += view_settings.get(namespace + '_user') or []
        cmds += view_settings.get(namespace + '_project') or []
        cmds += view_settings.get(namespace + '_language') or []

        # Return the collection of cmds
        return cmds

    def run_hooks(self, view, namespace):
        # Resolve the commands
        cmds = self.get_hooks(view, namespace)

        # For each command, run it
        for cmd in cmds:
            self.run_cmd(view, cmd)

    def run_cmd(self, view, cmd):
        # By default, run the command on the view
        scope = view

        # If there is a scope key
        scope_key = cmd.get('scope', None)
        if scope_key:
            # If it is app, move to app
            if scope_key == 'app':
                scope = sublime
            elif scope_key == 'window':
                # Otherwise if it is window, move to window
                scope = view.window() or sublime.active_window()
            else:
                # Otherwise, complain
                raise Exception('Scope key "%s" for `hooks` plugin was not recognized.')

        args = cmd.get('args', {})
        if view.window():
            variables = view.window().extract_variables()
            view_file_name = view.file_name()
            if view_file_name:
                # Instead of the current active file_name from
                # the variables, use the file_name from the view
                # from which the event was triggered.
                file_path = Path(view_file_name)
                variables["file"] = str(file_path)
                variables["file_path"] = str(file_path.parent)
                variables["file_base_name"] = file_path.stem
                # Path.suffix includes the '.' but sublime doesn't
                variables["file_extension"] = file_path.suffix[1:] if file_path.suffix else ""
                variables["file_name"] = file_path.name
            else:
                # Clear the file related variables when there is
                # no file_name associated with the view
                for key in ["file", "file_path", "file_base_name", "file_extension", "file_name"]:
                    if key in variables:
                        del variables[key]
            args = sublime.expand_variables(args, variables)

        # Run the command in its scope
        scope.run_command(cmd['command'], args)


# Set up all hooks
ST_HOOKS = [
    # ST2 / ST3 hooks
    'on_new',
    'on_clone',
    'on_load',
    'on_close',
    'on_pre_save',
    'on_post_save',
    # 'on_modified',  # Disabled for potential overrun
    # 'on_selection_modified',  # Disabled for potential overrun
    'on_activated',
    'on_deactivated',
    # 'on_query_context',  # Disabled for potential overrun

    # ST3 hooks
    'on_new_async',
    'on_clone_async',
    'on_load_async',
    'on_pre_close',
    'on_pre_save_async',
    'on_post_save_async',
    # 'on_modified_async',  # Disabled for potential overrun
    # 'on_selection_modified_async',  # Disabled for potential overrun
    'on_activated_async',
    'on_deactivated_async',
    # 'on_text_command',  # Disabled for potential overrun
    # 'on_window_command',  # Disabled for potential overrun
    # 'post_text_command',  # Disabled for potential overrun
    # 'post_window_command',  # Disabled for potential overrun
]

# For each hook, set it up
for namespace in ST_HOOKS:
    def create_run_hook(namespace):
        def run_hook_namespace(self, view):
            self.run_hooks(view, namespace)
        return run_hook_namespace
    setattr(HooksListener, namespace, create_run_hook(namespace))
