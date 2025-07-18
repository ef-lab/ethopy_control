let table;
let refreshInterval;
let setupOptionsInitialized = false;

$(document).ready(function() {
    // Initialize setup filter with bootstrap-select
    $('#setupFilter').selectpicker({
        liveSearch: true,
        actionsBox: true,
        selectedTextFormat: 'count > 3',
        countSelectedText: '{0} setups selected'
    });

    // Save original options once at the beginning
    const originalFilterOptions = [];
    $('#setupFilter option').each(function() {
        originalFilterOptions.push({
            value: $(this).val(),
            text: $(this).text()
        });
    });
    
    // Store original setup options for rebuilding
    const originalSetupOptions = [];
    $('#setupFilter option').each(function() {
        originalSetupOptions.push({
            value: $(this).val(),
            text: $(this).text()
        });
    });
    
    // Define the rebuildSetupFilter function
    function rebuildSetupFilter() {
        // Save current selections
        const currentSelections = $('#setupFilter').val() || [];
        
        // Clear and rebuild from original options
        $('#setupFilter').empty();
        originalSetupOptions.forEach(opt => {
            $('#setupFilter').append(`<option value="${opt.value}">${opt.text}</option>`);
        });
        
        // Restore selections and refresh
        $('#setupFilter').val(currentSelections);
        $('#setupFilter').selectpicker('destroy');
        $('#setupFilter').selectpicker({
            liveSearch: true,
            actionsBox: true,
            selectedTextFormat: 'count > 3',
            countSelectedText: '{0} setups selected'
        });
    }

    // Override the bootstrap-select refresh method to use our saved options
    const originalBootstrapSelectRefresh = $.fn.selectpicker.Constructor.prototype.refresh;
    $.fn.selectpicker.Constructor.prototype.refresh = function() {
        // Get current selections before refresh
        const currentSelections = this.$element.val() || [];
        
        // Remove all existing options
        this.$element.empty();
        
        // Add original options back
        originalFilterOptions.forEach(opt => {
            this.$element.append(new Option(opt.text, opt.value, false, currentSelections.includes(opt.value)));
        });
        
        // Now call the original refresh
        return originalBootstrapSelectRefresh.call(this);
    };

    // Initialize column visibility dropdown with bootstrap-select
    $('#columnVisibility').selectpicker({
        actionsBox: true,
        title: '<i class="fas fa-columns"></i> Columns',
        buttonClass: 'btn btn-outline-secondary'
    });

    // Initialize DataTable
    table = $('#controlTable').DataTable({
        ajax: {
            url: '/api/control-table',
            data: function(d) {
                return {
                    ...d,
                    'setups[]': $('#setupFilter').val()
                };
            },
            dataSrc: 'data' // Just return the data directly
        },
        columns: [
            {
                data: null,
                orderable: false,
                render: function(data) {
                    return `<input type="checkbox" class="form-check-input row-select" data-setup="${data.setup}">`;
                }
            },
            { 
                data: 'setup',
                render: function(data, type, row) {
                    const pingTime = new Date(row.last_ping);
                    const now = new Date();
                    const diffInMinutes = Math.floor((now - pingTime) / (1000 * 60));
                    
                    if (diffInMinutes > 5) {
                        return `<span class="text-vermillion">${data}</span>`;
                    } else {
                        return data;
                    }
                }
            },
            { 
                data: 'status',
                render: function(data) {
                    const statusClasses = {
                        'ready': 'bg-bluish-green',
                        'running': 'bg-blue',
                        'stop': 'bg-orange',
                        'exit': 'bg-vermillion'
                    };
                    return `<span class="badge ${statusClasses[data] || ''}">${data}</span>`;
                }
            },
            { data: 'animal_id' },
            { data: 'task_idx' },
            { data: 'session' },
            { data: 'trials' },
            { data: 'total_liquid' },
            { data: 'state' },
            { data: 'difficulty' },
            { data: 'start_time' },
            { data: 'stop_time' },
            { 
                data: 'last_ping',
                render: function(data) {
                    const pingTime = new Date(data);
                    const now = new Date();
                    const diffInMinutes = Math.floor((now - pingTime) / (1000 * 60));
                    
                    if (diffInMinutes > 5) {
                        return `<span class="text-vermillion">${data} <br> (ping > 5 min)</span>`;
                    } else {
                        return `${data}`;
                    }
                }
            },
            { data: 'notes' },
            { data: 'user_name' },
            { data: 'queue_size' },
            { data: 'ip_address' },
            {
                data: null,
                render: function(data) {
                    let buttons = `<button class="btn btn-sm btn-bluish-green edit-btn me-1" data-setup="${data.setup}">
                                      Edit
                                   </button>`;
                    
                    // Only add reboot button if IP is configured
                    if (data.ip_address) {
                        buttons += `<button class="btn btn-sm btn-vermillion reboot-btn" data-setup="${data.setup}" data-ip="${data.ip_address}">
                                       Reboot
                                    </button>`;
                    }
                    
                    return buttons;
                }
            }
        ],
        order: [[1, 'asc']],
        pageLength: 10,
        responsive: true,
        autoWidth: false,
        scrollX: true,
        language: {
            emptyTable: "No setups match the current filter"
        },
        dom: window.innerWidth < 768 ? 
            "<'row'<'col-sm-12'tr>>" +  // Just the table for mobile
            "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>" :  // Pagination and info
            "<'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>" +  // Length and filter
            "<'row'<'col-sm-12'tr>>" +  // Table
            "<'row'<'col-sm-12 col-md-5'i><'col-sm-12 col-md-7'p>>",  // Info and pagination
        createdRow: function(row, data, dataIndex) {
            // Check if last_ping is more than 5 minutes old
            const pingTime = new Date(data.last_ping);
            const now = new Date();
            const diffInMinutes = Math.floor((now - pingTime) / (1000 * 60));
            
            if (diffInMinutes > 5) {
                $(row).addClass('table-inactive');
            }
        },
        // Style the length menu
        initComplete: function() {
            // Select all options in the setup filter to show all setups
            $('#setupFilter option').prop('selected', true);
            // $('#setupFilter').selectpicker('refresh');
            
            // Style the DataTables length menu to match site theme
            $('.dataTables_length select').addClass('form-select form-select-sm').css('width', 'auto');
            
            // Add responsive classes to improve mobile display
            $('.dataTables_wrapper .row').addClass('g-3');
            $('.dataTables_length, .dataTables_filter').addClass('mb-2');
            
            // Hide less important columns on small screens automatically
            if (window.innerWidth < 768) {
                // Initially hide all optional columns on mobile
                applyMobileColumnVisibility();
            }
            
            // Adjust table styling to prevent column width changes
            table.columns.adjust().draw();
        },
        // Lock the dropdown options after initial load
        draw: function() {
            if (!setupOptionsInitialized) {
                setupOptionsInitialized = true;
                
                // Store original options for reference
                const originalOptions = $('#setupFilter option').clone();
                
                // Override bootstrap-select refresh method to prevent duplicates
                const originalRefresh = $.fn.selectpicker.Constructor.prototype.refresh;
                $.fn.selectpicker.Constructor.prototype.refresh = function() {
                    // Clear all options first
                    this.$element.find('option').remove();
                    // Re-add original options
                    this.$element.append(originalOptions.clone());
                    // Call original refresh
                    return originalRefresh.call(this);
                };
            }
        }
    });

    // Function to handle mobile-specific column visibility
    function applyMobileColumnVisibility() {
        // On mobile, determine how many columns to show based on screen width
        let essentialColumns;
        
        if (window.innerWidth < 480) {
            // For very small screens (portrait phones), show minimal columns
            essentialColumns = [1, 2]; // Only Setup and Status
        } else if (window.innerWidth < 768) {
            // For larger phones and small tablets
            essentialColumns = [1, 2, 3, 4]; // Setup, Status, Animal ID, Task Index
        } else {
            // Default set of columns for larger screens
            essentialColumns = [1, 2, 3, 4, 12, 14]; // Setup, Status, Animal ID, Task Index, Last Ping, User
        }
        
        for (let i = 1; i <= 17; i++) {
            if (!essentialColumns.includes(i)) {
                table.column(i).visible(false);
            } else {
                table.column(i).visible(true);
            }
        }
        
        // Update checkboxes to match
        $('.column-toggle').prop('checked', false);
        essentialColumns.forEach(colIndex => {
            $(`.column-toggle[value="${colIndex}"]`).prop('checked', true);
        });
        
        // Save this state
        saveColumnVisibility();
    }

    // Column toggle change handler
    $('.column-toggle').on('change', function() {
        const colIndex = parseInt($(this).val());
        
        // Prevent selecting too many columns on small screens
        if (window.innerWidth < 480) {
            // Count currently checked columns
            const checkedCount = $('.column-toggle:checked').length;
            
            // If trying to check a new column and already at limit
            if ($(this).prop('checked') && checkedCount > 5) {
                // Show warning and revert the change
                showNotification('Maximum 5 columns allowed on small screens', 'error');
                $(this).prop('checked', false);
                return;
            }
        }
        
        table.column(colIndex).visible($(this).prop('checked'));
        
        // Save column visibility state to localStorage
        saveColumnVisibility();
    });

    // Function to save column visibility state
    function saveColumnVisibility() {
        const visibleColumns = $('.column-toggle:checked').map(function() {
            return $(this).val();
        }).get();
        
        localStorage.setItem('columnVisibility', JSON.stringify(visibleColumns));
    }

    // Modified function to apply column visibility without causing spacing issues
    function applyColumnVisibility() {
        // Define required columns based on screen size
        let requiredColumns;
        
        if (window.innerWidth < 480) {
            // For very small screens (portrait phones), show minimal columns
            requiredColumns = [1, 2]; // Only Setup and Status
        } else if (window.innerWidth < 768) {
            // For larger phones and small tablets
            requiredColumns = [1, 2, 3, 4]; // Setup, Status, Animal ID, Task Index
        } else {
            // Default set of columns for larger screens
            requiredColumns = [1, 2, 3, 4, 12, 14]; // Setup, Status, Animal ID, Task Index, Last Ping, User
        }
        
        // Get saved visibility settings
        const savedColumnVisibility = localStorage.getItem('columnVisibility');
        const visibleColumns = savedColumnVisibility ? JSON.parse(savedColumnVisibility) : [];
        
        // Disable column auto-adjustment during visibility changes
        table.settings()[0].bAutoWidth = false;
        
        // Hide all optional columns first (except the checkbox column and required columns)
        for (let i = 1; i <= 17; i++) {
            if (!requiredColumns.includes(i)) {
                table.column(i).visible(false, false); // false to defer redrawing
            }
        }
        
        // Show selected optional columns
        visibleColumns.forEach(colIndex => {
            table.column(parseInt(colIndex)).visible(true, false); // false to defer redrawing
        });
        
        // Make sure required columns are always visible
        requiredColumns.forEach(colIndex => {
            table.column(colIndex).visible(true, false); // false to defer redrawing
        });
        
        // Now redraw the table with all the visibility changes at once
        table.columns.adjust().draw(false);
        
        // Update the checkbox states to match the visible columns
        $('.column-toggle').each(function() {
            const colIndex = parseInt($(this).val());
            $(this).prop('checked', visibleColumns.includes(colIndex.toString()) || requiredColumns.includes(colIndex));
        });
    }

    // Initialize column visibility after table is loaded
    setTimeout(function() {
        // If saved settings exist, apply them
        const savedColumnVisibility = localStorage.getItem('columnVisibility');
        if (savedColumnVisibility) {
            applyColumnVisibility();
        } else if (window.innerWidth < 768) {
            // On mobile with no saved settings, use mobile defaults
            applyMobileColumnVisibility();
        } else {
            // On desktop with no saved settings, show default columns
            applyColumnVisibility();
        }
    }, 100);

    // Set up refresh interval logic
    function setupRefreshInterval() {
        // Clear any existing interval
        if (refreshInterval) {
            clearInterval(refreshInterval);
            refreshInterval = null;
        }
        
        // Get selected interval
        const intervalValue = parseInt($('#refreshInterval').val());
        
        // Only set interval if greater than 0
        if (intervalValue > 0) {
            refreshInterval = setInterval(() => {
                table.ajax.reload(function() {
                    applyColumnVisibility();
                }, false);
            }, intervalValue);
            
            // Store user preference
            localStorage.setItem('refreshInterval', intervalValue);
        }
    }
    
    // Load saved refresh interval preference
    const savedInterval = localStorage.getItem('refreshInterval');
    if (savedInterval) {
        $('#refreshInterval').val(savedInterval);
    }
    
    // Set initial refresh interval
    setupRefreshInterval();
    
    // Refresh interval change handler
    $('#refreshInterval').change(function() {
        setupRefreshInterval();
    });

    // Add window resize handler to adjust columns on orientation change
    let resizeTimer;
    let lastOrientation = window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
    
    $(window).on('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Detect orientation change
            const currentOrientation = window.innerWidth > window.innerHeight ? 'landscape' : 'portrait';
            const isOrientationChange = currentOrientation !== lastOrientation;
            lastOrientation = currentOrientation;
            
            // If switching to portrait mode, enforce stricter column limits
            if (isOrientationChange && currentOrientation === 'portrait' && window.innerWidth < 768) {
                // Show a notification about the column limitation
                showNotification('Portrait mode detected. Column visibility adjusted for better viewing.', 'info');
                
                // Apply mobile-specific visibility for portrait mode
                applyMobileColumnVisibility();
            } else if (isOrientationChange && currentOrientation === 'landscape') {
                // When switching to landscape, we can show more columns
                applyColumnVisibility();
            }
            
            // Adjust table column widths after resize
            table.columns.adjust().draw(false);
        }, 250);
    });

    // Manual refresh button
    $('#refreshButton').click(() => {
        table.ajax.reload(function() {
            applyColumnVisibility();
        }, false);
    });

    // // Add quick filter buttons
    // const filterContainer = $('.bootstrap-select').after('<div class="mt-2"></div>').next();
    // filterContainer.append(`
    //     <div class="btn-group btn-group-sm mt-2" role="group">
    //         <button type="button" class="btn btn-outline-secondary filter-btn" data-filter="all">All</button>
    //         <button type="button" class="btn btn-outline-secondary filter-btn" data-filter="active">Active (< 10min)</button>
    //         <button type="button" class="btn btn-outline-secondary filter-btn" data-filter="ready">Ready</button>
    //         <button type="button" class="btn btn-outline-secondary filter-btn" data-filter="running">Running</button>
    //         <button type="button" class="btn btn-outline-secondary filter-btn" data-filter="error">Error</button>
    //     </div>
    // `);
    
    // // Filter button click handler - commented out since the buttons are no longer present
    // $('.filter-btn').click(function() {
    //     const filterType = $(this).data('filter');
    //     
    //     // Set active state on button
    //     $('.filter-btn').removeClass('active');
    //     $(this).addClass('active');
    //     
    //     // Rebuild filter to eliminate any duplicates
    //     rebuildSetupFilter();
    //     
    //     // Clear existing selections to start fresh
    //     $('#setupFilter').selectpicker('deselectAll');
    //     
    //     if (filterType === 'all') {
    //         // Select all options
    //         $('#setupFilter option').prop('selected', true);
    //     } else if (filterType === 'active') {
    //         // First reload to get fresh data
    //         table.ajax.reload(function() {
    //             // After data is loaded, filter based on last_ping
    //             const activeSetups = [];
    //             table.rows().every(function() {
    //                 const data = this.data();
    //                 const pingTime = new Date(data.last_ping);
    //                 const now = new Date();
    //                 const diffInMinutes = Math.floor((now - pingTime) / (1000 * 60));
    //                 
    //                 if (diffInMinutes < 5) {
    //                     activeSetups.push(data.setup);
    //                 }
    //             });
    //             
    //             // Select only active setups
    //             activeSetups.forEach(setup => {
    //                 $(`#setupFilter option[value="${setup}"]`).prop('selected', true);
    //             });
    //             
    //             // Refresh the selectpicker UI without causing duplicates
    //             $('#setupFilter').selectpicker('refresh');
    //             
    //             // Reload the table with the new filter
    //             table.ajax.reload(function() {
    //                 applyColumnVisibility();
    //             });
    //             updateBulkActionButton();
    //         });
    //         return; // Skip the normal flow
    //     } else {
    //         // Filter by status
    //         $(`#setupFilter option`).each(function() {
    //             const text = $(this).text();
    //             if (text.includes(`(${filterType})`) || 
    //                 (filterType === 'stop' && text.includes('(Stopped)'))) {
    //                 $(this).prop('selected', true);
    //             }
    //         });
    //     }
    //     
    //     // Refresh the selectpicker UI without causing duplications
    //     $('#setupFilter').selectpicker('refresh');
    //     
    //     // Reload the table with the new filter and reapply column visibility
    //     table.ajax.reload(function() {
    //         applyColumnVisibility();
    //     });
    //     updateBulkActionButton();
    // });
    
    // Setup filter change handler
    $('#setupFilter').on('changed.bs.select', function() {
        // Just reload the table data with current filter values
        // Do NOT update the dropdown options
        table.ajax.reload(null, false);
        updateBulkActionButton();
    });

    // Add select all checkbox handler
    $('#selectAll').change(function() {
        $('.row-select').prop('checked', $(this).prop('checked'));
        updateBulkActionButton();
    });

    // Column visibility change handler
    $('#columnVisibility').on('changed.bs.select', function() {
        const selectedColumns = $(this).val();
        
        // Hide all columns first (except the checkbox column)
        for (let i = 1; i <= 17; i++) {
            table.column(i).visible(false);
        }
        
        // Show only selected columns
        selectedColumns.forEach(colIndex => {
            table.column(parseInt(colIndex)).visible(true);
        });
        
        // Save column visibility state to localStorage
        localStorage.setItem('columnVisibility', JSON.stringify(selectedColumns));
    });

    // Row checkbox handler
    $('#controlTable').on('change', '.row-select', function() {
        updateBulkActionButton();
        // Update select all checkbox state
        const totalCheckboxes = $('.row-select').length;
        const checkedCheckboxes = $('.row-select:checked').length;
        $('#selectAll').prop({
            'checked': checkedCheckboxes === totalCheckboxes,
            'indeterminate': checkedCheckboxes > 0 && checkedCheckboxes < totalCheckboxes
        });
    });

    // Bulk status change handler
    $('#bulkStatus').change(function() {
        updateBulkActionButton();
    });

    // Apply bulk action handler
    $('#applyBulkAction').click(function() {
        const selectedSetups = $('.row-select:checked').map(function() {
            return $(this).data('setup');
        }).get();

        const updates = {
            status: $('#bulkStatus').val()
        };

        $.ajax({
            url: '/api/control-table/bulk-update',
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify({
                setups: selectedSetups,
                updates: updates
            }),
            success: function(response) {
                table.ajax.reload(function() {
                    applyColumnVisibility();
                }, false);
                showNotification(`Successfully updated ${response.updated_count} setups`, 'success');
                $('#bulkStatus').val('');
                $('#selectAll').prop('checked', false);
                updateBulkActionButton();
            },
            error: function(xhr) {
                const error = xhr.responseJSON?.error || 'An error occurred';
                showNotification(error, 'error');
            }
        });
    });

    // Edit button click handler
    $('#controlTable').on('click', '.edit-btn', function() {
        const setup = $(this).data('setup');
        const row = table.row($(this).closest('tr')).data();

        $('#editSetup').val(setup);
        $('#editStatus').val(''); // Default to "Keep Current Status"
        $('#editAnimalId').val(row.animal_id);
        $('#editTaskIdx').val(row.task_idx);
        $('#editIpAddress').val(row.ip_address);
        $('#editStartTime').val(row.start_time);
        $('#editStopTime').val(row.stop_time);
        $('#editUserName').val(row.user_name);

        // Disable invalid status transitions
        const status = row.status;
        $('#editStatus option').prop('disabled', true);
        
        // Always enable the empty option
        $('#editStatus option[value=""]').prop('disabled', false);
        
        if (status === 'ready') {
            $('#editStatus option[value="running"]').prop('disabled', false);
        } else if (status === 'running') {
            $('#editStatus option[value="stop"]').prop('disabled', false);
        } else if (status === 'sleeping') {
            $('#editStatus option[value="stop"]').prop('disabled', false);
        }

        $('#editModal').modal('show');
    });
    
    // Reboot button click handler
    $('#controlTable').on('click', '.reboot-btn', function() {
        const setup = $(this).data('setup');
        const ip = $(this).data('ip');
        
        if (!confirm(`Are you sure you want to reboot ${setup} (${ip})? This will interrupt any running experiments.`)) {
            return;
        }
        
        // Show loading state
        const $btn = $(this);
        const originalText = $btn.html();
        $btn.html('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Rebooting...');
        $btn.prop('disabled', true);
        
        $.ajax({
            url: `/api/control-table/${setup}/reboot`,
            method: 'POST',
            contentType: 'application/json',
            success: function(response) {
                showNotification(`Reboot command sent to ${setup} successfully`, 'success');
                // Reset button after 5 seconds to allow for reboot
                setTimeout(() => {
                    $btn.html(originalText);
                    $btn.prop('disabled', false);
                }, 60000);
            },
            error: function(xhr) {
                const error = xhr.responseJSON?.error || 'An error occurred during reboot';
                showNotification(error, 'error');
                // Reset button
                $btn.html(originalText);
                $btn.prop('disabled', false);
            }
        });
    });

    // Save changes handler
    $('#saveChanges').click(function() {
        const setup = $('#editSetup').val();
        const data = {
            animal_id: $('#editAnimalId').val(),
            task_idx: parseInt($('#editTaskIdx').val()),
            ip_address: $('#editIpAddress').val(),
            start_time: $('#editStartTime').val(),
            stop_time: $('#editStopTime').val(),
            user_name: $('#editUserName').val()
        };
        
        // Only include status if a value is selected
        const status = $('#editStatus').val();
        if (status) {
            data.status = status;
        }

        $.ajax({
            url: `/api/control-table/${setup}`,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: function(response) {
                $('#editModal').modal('hide');
                table.ajax.reload(function() {
                    applyColumnVisibility();
                }, false);
                showNotification('Record updated successfully', 'success');
            },
            error: function(xhr) {
                const error = xhr.responseJSON?.error || 'An error occurred';
                showNotification(error, 'error');
            }
        });
    });

    // Mobile-specific controls
    $('#mobileRefreshBtn').on('click', function() {
        refreshData();
    });
    
    // Mobile search box
    $('#mobileSearchBox').on('keyup', function() {
        table.search($(this).val()).draw();
    });
    
    // Hide the default DataTables search box on mobile
    if (window.innerWidth < 768) {
        $('.dataTables_filter').hide();
    }
});

function updateBulkActionButton() {
    const hasSelection = $('.row-select:checked').length > 0;
    const hasStatusSelected = $('#bulkStatus').val() !== '';
    $('#applyBulkAction').prop('disabled', !(hasSelection && hasStatusSelected));
}

function showNotification(message, type) {
    Toastify({
        text: message,
        duration: 3000,
        gravity: "top",
        position: 'right',
        backgroundColor: type === 'success' ? '#198754' : '#dc3545',
        stopOnFocus: true
    }).showToast();
}

// Cleanup on page unload
window.addEventListener('unload', function() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
});

// Define the refreshData function
function refreshData() {
    // Clear any search/filter that might be active
    table.search('').columns().search('').draw();
    
    // Reload data from server with current filters
    table.ajax.reload(function() {
        applyColumnVisibility();
    }, false);
}

// Set up event handlers for standard controls
$('#refreshButton').on('click', function() {
    refreshData();
});