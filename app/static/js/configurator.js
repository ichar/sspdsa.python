// **********************************************
// APPLICATION PAGE DECLARATION: /configurator.js
// ----------------------------------------------
// Version: 1.00
// Date: 28-10-2022

default_submit_mode = 2;
default_action      = '400';
default_log_action  = '401';
default_input_name  = 'change_id';
default_menu_item   = '';
default_handler     = null; //function(x) { $PageLoader.refresh(x); };
default_params      = {}; //{ 'max-width': $_width('client') };

LINE    = '';
SUBLINE = '';

var is_full_container = 0;

// Flag for 'input' keyboards
var is_input_focused = 0;
var is_no_line_open = 0;

var current_controller = 'configs';

// ----------------------
// Dialog Action Handlers
// ----------------------

function sidebar_callback() {
    $onInfoContainerChanged();
}

function subline_refresh(filename) {
    $(".filename").each(function() { 
        $(this).html(filename);
    });
}

function log_callback_error(action, errors) {
    if (IsTrace)
        alert('log_callback_error.action:'+action);
}

function log_callback(current_action, data, props) {
    var is_error = getattr(props, 'is_error', 0);
    var message = getattr(props, 'message', null);
    var is_message = !is_empty(message);

    if (IsDebug)
        alert('configurator.log_callback:'+message+':'+is_error);
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['type', 'status', 'batchtype']);

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    $TabSelector.init();

    tab_init(current_controller, 0);

    init_controller(current_controller);

    // ------------------------
    // Start default log action
    // ------------------------

    interrupt(true, 1);
}

function $Confirm(mode, ob) {
    $ConfirmDialog.close();

    function _check(x) { 
        var errors = x['errors']; 

        //alert(errors.length);

        if (errors.length > 0) {
            var msg = errors.join('<br>');
            $ShowError(msg, true, true, false);
        }
        else {
            $NotificationDialog.open(keywords['Message:Request sent successfully']);
        }
    }

    ob = $("#config_content");

    switch (mode) {
    case 0:
        selected_menu_action = default_log_action;
        $onLineFormSubmit();
        break;
    case 1:
        if (confirm_action == 'save') {
            //var ids = SelectedGetItem(SUBLINE, 'id');
            //$("input[name='selected_batch_ids']").each(function() { $(this).val(ids); });

            $("#command").val('admin:'+confirm_action);
            $PageLoader.handle_change($("#config_content"), confirm_action);
        }
        else if (confirm_action == 'restore') {
            $("#command").val('admin:'+confirm_action);
            $onParentFormSubmit('config-form');
        }
        break;
    }
}

function $Notification(mode, ob) {
    $NotificationDialog.close();
}

function $onTabSelect(group) {

}

function $onTablineSelect(ob, alias) {
    console.log('configurator.$onTablineSelect.selector:', selector);
    if (!is_empty(selector))
        $ConfiguratorSubmitDialog.activate(current_controller);
}

function $ShowMenu(id, status, path) {
}

function $onPaginationFormSubmit(frm) {
    return true;
}

function $onFilterFormSubmit(frm) {
    return true;
}

function $onInfoContainerChanged() {
}

// ===========================
// Dialog windows declarations
// ===========================

function $onFormSubmit(frm) {
    if (IsTrace)
        alert('references.pagging-from submit');
}

function MakeFilterSubmit(mode, page) {
    //$("#filter-form").attr("action", baseURI);
}

function makeTodayRequest() {
}

// =========================
// Custom routine assigments
// =========================

function runSave() {
    confirm_action = 'save';

    $InProgress(null);

    $ConfirmDialog.open(keywords['Command:Do you really want to save changes'], 0, 186);

    is_input_focused = false;
}

function runRestore(x) {
}

function activateSave() {
    $("#page_save").removeClass('disabled').attr('disabled', false).show();
}

function $PageButton(ob) {
    var id = ob.attr("id");
    var x = id.split('_');
    var command = x.length >= 2 ? x[1] : x[0];
    
    //alert(id);

    $InProgress(ob, 1);

    switch (command) {
        case 'save':
            runSave();
            break;
        case 'restore':
            $runRestore();
            break;
    }
}

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{

    // ---------------------
    // Data Section progress
    // ---------------------

    $("#config_content").click(function(e) {
        $PageScroller.deactivate_group();
        is_input_focused = true;
    });

    $("#messages_content").click(function(e) {
        $PageScroller.deactivate_group();
    });

    $("#config-form").on('click', 'textarea', function(e) {
        is_input_focused = true;
    }).on('focusout', function(e) {
        is_input_focused = false;
    });

    // -----------------
    // Tabline selection
    // -----------------

    $("#tabline-configs").on('click', '.column', function(e) {
        //
        //   Tabline Columns click
        //
        if ($PageLoader.is_shown)
            return;

        var ob = ($(this)).parent();

        if (IsTrace)
            alert('configurator.click.column:'+ob.attr('id'));

        $PageScroller.init_state(ob);

        e.stopPropagation();
    });

    $("#configs").on('click', '.row-button', function(e) {
        //
        //   Tabline Navigate Buttons Cursor Controller click
        //
        var ob = $(this).children('a').eq(0);
        var id = ob.attr('id');
        var link = id.split(':')[1];
        var x = link.split('_');
        var group = x[0];
        var command = x[1];
    
        if (IsTrace)
            alert('configurator.click.row-button:'+joinToPrint([group, command]));

        $PageScroller.refresh(group, command);

        e.preventDefault();
        e.stopPropagation();
    });

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    // -----------------
    // Page Form Buttons
    // -----------------

    $("button[id^='page']", this).click(function(e) {
        $PageButton($(this));
        e.preventDefault();
    });

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $PageScroller.reset(1, 1000);
    });

    $(window).scroll(function(e){
        //$PageScroller.checkPosition(0);
    });

    // --------
    // Keyboard
    // --------

    $(window).keydown(function(e) {
        if ($ConfirmDialog.is_focused() || $NotificationDialog.is_focused())
            return;

        if (is_show_error)
            return;

        if (e.keyCode==13) {                                     // Enter
            // ------------------------------------
            // Bankpesro Submit Dialog Class Events
            // ------------------------------------
            if ($ConfiguratorSubmitDialog.is_focused()) {
                $ConfiguratorSubmitDialog.confirmed();
                e.preventDefault();
                return false;
            }
        }

        if ($ConfiguratorSubmitDialog.is_focused() || is_search_focused)
            return;

        var exit = false;

        //alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        if (is_input_focused) {
            activateSave();
            return;
        }
        
        if (e.shiftKey && e.keyCode==9) {                       // Shift-Tab
            init_controller(null);
            exit = true;
        }

        else if (e.shiftKey && e.keyCode==79) {                 // Shift-O
            e.stopPropagation();
            $SidebarDialog.activate($(this));
            exit = true;
        }

        // -----------------------
        // Tabline Selector moving
        // -----------------------

        if (selector.active) {
            exit = true;
            if (e.keyCode==38)                                  // Up
                $PageScroller.refresh(null, 'up');
            else if (e.keyCode==40)                             // Down
                $PageScroller.refresh(null, 'down');
            else if (e.keyCode==36)                             // Home
                $PageScroller.refresh(null, 'first');
            else if (e.keyCode==33)                             // PgUp
                $PageScroller.refresh(null, 'pgup');
            else if (e.keyCode==34)                             // PgDown
                $PageScroller.refresh(null, 'pgdown');
            else if (e.keyCode==35)                             // End
                $PageScroller.refresh(null, 'last');
            else
                exit = false;
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function search_is_empty() {
    return is_empty($("#searched").val()) ? true : false;
}

function page_is_focused(e) {
    return 0; //$ConfiguratorSubmitDialog.is_focused();
}

function $_show_page(mode) {
    $ShowPage(mode);
}

function resize(force){
    // orion  viewport::1043:1043:screen::1200:avail::1152:client::862:1043:862:inner-outer::1043:1128: max::1200
    // asus:  viewport::794:794:screen::900:avail::900:client:1052:1052:1052:inner-outer::794:900: max::1052
    // note:  viewport::635:635:screen::768:avail::741:client::1104:1104:1104:inner-outer::635:741: max::1104
    //
    //show_height();
    var max_height = $_height('max');
    var is_max = win_is_max_height();
    var s, x1, x2, x3;
    var devscreen = 900;
    var viewport = verge.viewportH();
    if (is_max) {
        s = Math.max(window.screen.height, window.outerHeight) / devscreen;
        x1 = s*(window.screen.height >= devscreen) ? 0.48 : 0.128;
        x2 = s*(window.screen.height >= devscreen) ? 0.42 : 0.128;
        x3 = s*(window.screen.height >= devscreen) ? 0.40 : 0.128;
    } else {
        s = Math.max(window.screen.height, window.outerHeight) / devscreen;
        x1 = s*(window.screen.height >= devscreen) ? 0.612 : 0.128; //378
        x2 = s*(window.screen.height >= devscreen) ? 0.564 : 0.128; //306
        x3 = s*(window.screen.height >= devscreen) ? 0.552 : 0.128; //282
    }
    var height1 = Math.ceil(viewport*x1)-10;
    var height2 = Math.ceil(viewport*x2)-5;
    var height3 = Math.ceil(viewport*x3/2)-4;

    //alert(joinToPrint(['references.resize.height:', height1, max_height, is_max, x1]));

    var box1 = $("#config_content").css("height", $_get_css_size(height1, 'px'));
    var box2 = $("#tabline-configs").css("height", $_get_css_size(height2, 'px'));

    $(".change").each(function() { 
        $(this).css("height", $_get_css_size(int(height3), 'px'));
        //$(this).height(height);
    });

    //if (!(force || is_max)) $onLineFormSubmit();

    if (force) {
        init_controller();
    }

    //show_height();
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (configurator)');

    IsLog = 1;
    IsDebug = 0;
    IsDeepDebug = 0;
    IsTrace = 0;

    current_context = 'configurator';

    $("#search-context").attr("placeholder", "Найти (имя файла, ТЗ)...");

    //resize(1);

    IsActiveScroller = 0;

    $_init();
});
