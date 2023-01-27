// *******************************************
// APPLICATION PAGE DECLARATION: /spologger.js
// -------------------------------------------
// Version: 1.00
// Date: 28-10-2022

default_submit_mode = 2;
default_action      = '300';
default_log_action  = '301';
default_input_name  = 'log_id';
default_menu_item   = 'data-menu-batches';

LINE    = 'spologs';
SUBLINE = '';

var batch_can_be_activated = 0;
var postonline_path = null;

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

function log_callback(current_action, data, props) {
    batch_can_be_activated = (props && 'activate' in props) ? props['activate'] : 0;
}

function indigo(s) {
    $NotificationDialog.open('<img class="indigo_image" src="'+s+'" title="Indigo Design" alt>', 800, 620, keywords['Image view']);
}

// --------------
// Page Functions
// --------------

function $Init() {
    $SidebarControl.init(sidebar_callback, ['type', 'batchtype']); //'status', 

    page_sort_title = $("#sort_icon").attr('title');

    SelectedReset();

    //$LineSelector.init();
    //$SublineSelector.init();
    //$ShowMenu(default_menu_item);
    //$TabSelector.init();

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

    switch (mode) {
        case 0:
            break;
    }
}

function $Notification(mode, ob) {
    $NotificationDialog.close();

    if (confirm_action == 'materials') {
        var ob = $LineSelector.get_current();
        $onToggleSelectedClass(LINE, ob, 'submit', null);
    }
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
    //alert($_width('screen-min')-$("#sidebarFrame").width()+':'+$("#line-table").width());
}

function $onTabSelect(ob) {
    return true;
}

// ===========================
// Dialog windows declarations
// ===========================

function MakeFilterSubmit(mode, page) {
    // XXX
    //$("#filter-form").attr("action", baseURI);

    switch (mode) {

        // -------------
        // Submit modes:
        // -------------

        case 0:
        case 1:
        case 2:
        case 3:
        case 4:
        case 5:
            break;

        // ---------------------------
        // LineSelector Handler submit
        // ---------------------------

        case 9:
    }

    $ResetLogPage();

    $setPaginationFormSubmit(page);
    $onParentFormSubmit('filter-form');
}

function makeTodayRequest() {
    var date = new Date();
    var now = date.getToday();

    $_set_body_value('order-date-from', now);
    $onParentFormSubmit('filter-form');
}

// =========================
// Custom routine assigments
// =========================

// ====================
// Page Event Listeners
// ====================

jQuery(function($) 
{
    // --------------
    // Line selection
    // --------------

    // -----------------
    // SubLine selection
    // -----------------

    // ---------------------
    // Data Section progress
    // ---------------------

    // -----------------
    // Tabline selection
    // -----------------

    // ------------------------
    // Control Panel Menu items
    // ------------------------

    // ---------------------
    // Main Operator Buttons
    // ---------------------

    // --------------
    // Tabs Data menu
    // --------------

    // -------------
    // Resize window
    // -------------

    $(window).on("resize", function() {
        $PageScroller.reset(false);
    });

    $(window).scroll(function(e){
        $PageScroller.checkPosition(0);
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
            if ($SpologgerSubmitDialog.is_focused()) {
                $SpologgerSubmitDialog.confirmed();
                e.preventDefault();
                return false;
            }
        }

        if ($SpologgerSubmitDialog.is_focused() || is_search_focused)
            return;

        var exit = false;

        //alert(e.ctrlKey+':'+e.shiftKey+':'+e.altKey+':'+e.keyCode);

        if (e.shiftKey && e.keyCode==79) {                  // Shift-O
            e.stopPropagation();
            $SidebarDialog.activate($(this));
            exit = true;
        }

        if (exit) {
            e.preventDefault();
            return false;
        }
    });
});

function sidebar_submit() {
    if (IsDeepDebug) {
        alert('sidebar_submit.state:'+$("#sidebar").val());
    }
}

function page_is_focused(e) {
    return $SpologgerSubmitDialog.is_focused();
}

function $_show_page(mode) {
    $ShowPage(mode);
}

function resize(force) {
    if ($_mobile() && force) {
        //show_width();
        //show_height();

        var viewportW = verge.viewportW();
        var viewportH = verge.viewportH();

        //alert(viewportW+':'+ viewportH);
    }

    //var per_page = int($("#per_page").val());
    //alert(per_page);
    var size = int(30*per_page);
    $("#lines_container").height(size);
}

// =======
// STARTER
// =======

$(function() 
{
    if (IsTrace)
        alert('Document Ready (spologger)');

    IsLog = 1;

    current_context = 'main';

    $("#search-context").attr("title", search_title);
    //$("#batchtype").css("width", $("#status").width()+"px");
    //$("#batchtype").width($("#status").width());

    IsActiveScroller = 0;

    resize(1);

    $_init();
});
