/**
 * Roster Management JavaScript
 * Handles client-side interactions for the roster page
 */
$(document).ready(function() {
    // Add shift button click handler
    $('.add-shift-btn').on('click', function(e) {
        e.preventDefault();
        const linkingId = $(this).data('linking-id');
        const shiftDate = $(this).data('date');
        const formattedDate = formatDate(shiftDate);
        
        // Reset the form
        $('#shift-form')[0].reset();
        $('#linking-id').val(linkingId);
        $('#shift-date').val(shiftDate);
        $('#shift-id').val('');
        $('#is-edit').val('false');
        $('#is-rdo').prop('checked', false);
        $('#modal-title').text(`New Shift - ${formattedDate}`);
        
        // If an employee is selected, auto-select in the dropdown
        if (linkingId) {
            $('#staff-select').val(linkingId);
        }
        
        // Enable/disable time inputs
        enableTimeInputs();
        
        // Show modal
        $('#shift-modal').removeClass('hidden');
        
        // Calculate shift length
        calculateShiftLength();
    });
    
    // Edit shift button handler
    $('.edit-shift-btn').on('click', function(e) {
        e.preventDefault();
        const linkingId = $(this).data('linking-id');
        const shiftDate = $(this).data('date');
        const formattedDate = formatDate(shiftDate);
        
        // Set edit mode flag
        $('#is-edit').val('true');
        $('#modal-title').text(`Edit Shift - ${formattedDate}`);
        
        // Fetch shift data from API
        $.ajax({
            url: `/business/api/rostering/shifts?linking_id=${linkingId}&start_date=${shiftDate}&end_date=${shiftDate}`,
            type: 'GET',
            success: function(response) {
                if (response && response.length > 0) {
                    const shift = response[0];
                    
                    // Populate form with shift data
                    $('#linking-id').val(shift.linking_id);
                    $('#shift-date').val(shiftDate);
                    $('#shift-id').val(shift._id);
                    $('#shift-notes').val(shift.notes || '');
                    $('#is-rdo').prop('checked', shift.is_rdo);
                    
                    if (!shift.is_rdo) {
                        // Set time values
                        const startTime = shift.start_time ? new Date(shift.start_time).toTimeString().slice(0, 5) : '09:00';
                        const endTime = shift.end_time ? new Date(shift.end_time).toTimeString().slice(0, 5) : '17:00';
                        
                        $('#start-time').val(startTime);
                        $('#finish-time').val(endTime);
                    }
                    
                    // Populate selects if data available
                    if (shift.venue_id) {
                        $('#venue-select').val(shift.venue_id);
                    }
                    
                    if (shift.work_area_id) {
                        $('#work-area-select').val(shift.work_area_id);
                    }
                    
                    // Update UI based on RDO status
                    if (shift.is_rdo) {
                        disableTimeInputs();
                    } else {
                        enableTimeInputs();
                    }
                    
                    // Calculate shift length
                    calculateShiftLength();
                    
                    // Show modal
                    $('#shift-modal').removeClass('hidden');
                } else {
                    alert('Could not find shift data');
                }
            },
            error: function() {
                alert('Error fetching shift data');
            }
        });
    });
    
    // Add new employee button handler
    $('#add-employee-btn').on('click', function(e) {
        e.preventDefault();
        $('#employee-search').val('');
        $('#employee-list tr').show();
        $('#employee-modal').removeClass('hidden');
    });
    
    // Select employee from modal
    $('.select-employee-btn').on('click', function() {
        const linkingId = $(this).data('linking-id');
        const name = $(this).data('name');
        
        // TODO: Server-side implementation to add the employee row to the roster
        // For now, we'll just redirect to refresh the page with the employee added
        window.location.href = `/business/rostering?linking_id=${linkingId}`;
    });
    
    // Form submit handler
    $('#shift-form').on('submit', function(e) {
        e.preventDefault();
        
        const linkingId = $('#linking-id').val() || $('#staff-select').val();
        const shiftDate = $('#shift-date').val();
        const isEdit = $('#is-edit').val() === 'true';
        const shiftId = $('#shift-id').val();
        const isRDO = $('#is-rdo').prop('checked');
        
        if (!linkingId) {
            alert('Please select a staff member');
            return;
        }
        
        if (!shiftDate) {
            alert('Invalid shift date');
            return;
        }
        
        let shiftData = {
            linking_id: linkingId,
            venue_id: $('#venue-select').val(),
            date: shiftDate,
            is_rdo: isRDO,
            notes: $('#shift-notes').val()
        };
        
        if ($('#work-area-select').val()) {
            shiftData.work_area_id = $('#work-area-select').val();
        }
        
        if (!isRDO) {
            // Only include times for regular shifts
            const startTime = $('#start-time').val();
            const endTime = $('#finish-time').val();
            
            if (!startTime || !endTime) {
                alert('Please provide both start and end times');
                return;
            }
            
            // Convert to ISO format
            shiftData.start_time = `${shiftDate}T${startTime}:00`;
            shiftData.end_time = `${shiftDate}T${endTime}:00`;
        }
        
        // Determine if creating new or updating existing shift
        const url = isEdit ? 
            `/business/api/rostering/shifts/${shiftId}` : 
            '/business/api/rostering/shifts';
        
        const method = isEdit ? 'PUT' : 'POST';
        
        // Send to API
        $.ajax({
            url: url,
            type: method,
            contentType: 'application/json',
            data: JSON.stringify(shiftData),
            success: function(response) {
                // Close modal
                $('#shift-modal').addClass('hidden');
                
                // Reload page to show updated roster
                window.location.reload();
            },
            error: function(xhr) {
                let errorMsg = 'Failed to save shift';
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMsg = xhr.responseJSON.error;
                }
                alert(errorMsg);
            }
        });
    });
    
    // Apply filters button click handler
    $('#apply-filters').on('click', function() {
        const startDate = $('#start-date').val();
        const linkingId = $('#employee-filter').val();
        const venueId = $('#venue-filter').val();
        const workAreaId = $('#work-area-filter').val();
        
        // Build URL with query parameters
        let url = '/business/rostering?';
        if (startDate) url += `start_date=${startDate}&`;
        if (linkingId) url += `linking_id=${linkingId}&`;
        if (venueId) url += `venue_id=${venueId}&`;
        if (workAreaId) url += `work_area_id=${workAreaId}&`;
        
        // Remove trailing & if present
        url = url.endsWith('&') ? url.slice(0, -1) : url;
        
        // Navigate to filtered view
        window.location.href = url;
    });
    
    // Add keyboard event to close modals with ESC key
    $(document).on('keydown', function(e) {
        if (e.key === 'Escape') {
            $('#shift-modal').addClass('hidden');
            $('#employee-modal').addClass('hidden');
        }
    });
    
    // Close modals when clicking outside the form
    $('#shift-modal, #employee-modal').on('click', function(e) {
        if (e.target === this) {
            $(this).addClass('hidden');
        }
    });
    
    // Helper functions
    function formatDate(dateString) {
        const date = new Date(dateString);
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        return date.toLocaleDateString('en-US', options);
    }
    
    function enableTimeInputs() {
        const timeInputs = $('#start-time, #finish-time');
        timeInputs.prop('disabled', false);
        timeInputs.parent().removeClass('opacity-50');
    }
    
    function disableTimeInputs() {
        const timeInputs = $('#start-time, #finish-time');
        timeInputs.prop('disabled', true);
        timeInputs.parent().addClass('opacity-50');
    }
    
    // Initialize time calculation
    function calculateShiftLength() {
        const startTime = $('#start-time').val();
        const finishTime = $('#finish-time').val();
        const isRDO = $('#is-rdo').prop('checked');
        
        if (isRDO) {
            $('#shift-length').text('RDO');
            $('#shift-cost').text('$0.00');
            return;
        }

        if (startTime && finishTime) {
            const start = new Date(`1970-01-01T${startTime}:00`);
            const finish = new Date(`1970-01-01T${finishTime}:00`);
            
            // Handle overnight shifts
            let diff;
            if (finish < start) {
                const oneDayMs = 24 * 60 * 60 * 1000;
                diff = ((finish.getTime() + oneDayMs) - start.getTime()) / (1000 * 60 * 60);
            } else {
                diff = (finish - start) / (1000 * 60 * 60);
            }
            
            $('#shift-length').text(diff > 0 ? `${diff.toFixed(1)} hours` : 'Invalid time range');
            
            // Calculate approximate cost
            const avgPayRate = 29.75; // Default if not available
            const shiftCost = diff > 0 ? diff * avgPayRate : 0;
            $('#shift-cost').text(`$${shiftCost.toFixed(2)}`);
        } else {
            $('#shift-length').text('-');
            $('#shift-cost').text('-');
        }
    }
});
