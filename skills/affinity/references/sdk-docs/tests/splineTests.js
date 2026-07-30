'use strict';
const { Spline, SplineProfile, Point } = require('/geometry');

function testSpline() {
    // ============================================================================
    // BASIC CREATION TESTS
    // ============================================================================
    
    // Test 1: Create empty spline
    let spline1 = Spline.create();
    console.assert(spline1.pointCount === 0, "Empty spline should have 0 points");
    
    // Test 2: Create spline from profile
    let spline2 = Spline.createFromProfile(SplineProfile.Linear);
    console.assert(spline2.pointCount >= 0, "Linear spline should be created");
    
    let spline3 = Spline.createFromProfile(SplineProfile.SCurve);
    console.assert(spline3.pointCount >= 0, "SCurve spline should be created");
    
    // Test 3: Create spline from points array (all between 0-1)
    let points = [
        {x: 0.0, y: 0.0},
        {x: 0.25, y: 0.5},
        {x: 0.5, y: 1.0},
        {x: 0.75, y: 0.75},
        {x: 1.0, y: 0.0}
    ];
    
    let spline4 = Spline.createFromPoints(points);
    console.assert(spline4.pointCount === 5, "Spline from points should have 5 points");
    
    // ============================================================================
    // POINT MANAGEMENT TESTS
    // ============================================================================
    
    let testSpline = Spline.create();
    
    // Test insertPoint - simple insertion
    testSpline.insertPoint(new Point(0.1, 0.2));
    testSpline.insertPoint(new Point(0.3, 0.4));
    testSpline.insertPoint(new Point(0.5, 0.6));
    console.assert(testSpline.pointCount === 3, "Should have 3 points after insertPoint");
    
    // Test getPoint
    const point0 = testSpline.getPoint(0);
    console.assert(point0.x === 0.1 && point0.y === 0.2, "Point 0 should be (0.1, 0.2)");
    
    const point1 = testSpline.getPoint(1);
    console.assert(point1.x === 0.3 && point1.y === 0.4, "Point 1 should be (0.3, 0.4)");
    
    const point2 = testSpline.getPoint(2);
    console.assert(point2.x === 0.5 && point2.y === 0.6, "Point 2 should be (0.5, 0.6)");
    
    // Test replaceOrInsertPoint - should replace existing point if x already exists
    testSpline.replaceOrInsertPoint(new Point(0.3, 0.8)); // Same x as previous point
    console.assert(testSpline.pointCount === 3, "Point count should remain 3 after replaceOrInsertPoint");
    
    // Verify the replacement worked
    const replacedPoint = testSpline.getPoint(1); // Should be the point at index 1
    console.assert(replacedPoint.x === 0.3 && replacedPoint.y === 0.8, "Point at index 1 should be replaced with (0.3, 0.8)");
    
    // Test findPoint functionality
    const findResult1 = testSpline.findPoint(new Point(0.1, 0.2));
    console.assert(findResult1.isValid, "Should find point (0.1, 0.2)");
    
    const findResult2 = testSpline.findPoint(new Point(0.3, 0.8));
    console.assert(findResult2.isValid, "Should find point (0.3, 0.8)");
    
    const findResult3 = testSpline.findPoint(new Point(0.7, 0.3)); // Should not be found
    console.assert(!findResult3.isValid, "Should not find point (0.7, 0.3)");
    
    // Test removePoint
    const pointCountBeforeRemoval = testSpline.pointCount;
    testSpline.removePoint(1); // Remove the point at index 1
    console.assert(testSpline.pointCount === pointCountBeforeRemoval - 1, "Point count should decrease by 1 after removal");
    
    // Verify removal worked - point at index 1 should now be the old point at index 2
    const pointAfterRemoval = testSpline.getPoint(1);
    console.assert(pointAfterRemoval.x === 0.5 && pointAfterRemoval.y === 0.6, "Point at index 1 after removal should be (0.5, 0.6)");
    
    // Test clear
    testSpline.clear();
    console.assert(testSpline.pointCount === 0, "Point count should be 0 after clear");
    
    // ============================================================================
    // CLONING TESTS
    // ============================================================================
    
    let originalSpline = Spline.createFromPoints([
        {x: 0.0, y: 0.0},
        {x: 0.5, y: 1.0},
        {x: 1.0, y: 0.0}
    ]);
    
    console.assert(originalSpline.pointCount === 3, "Original spline should have 3 points");
    
    let clonedSpline = originalSpline.clone();
    console.assert(clonedSpline.pointCount === 3, "Cloned spline should have 3 points");
    
    // Verify they have the same points
    for (let i = 0; i < originalSpline.pointCount; i++) {
        const origPoint = originalSpline.getPoint(i);
        const clonePoint = clonedSpline.getPoint(i);
        console.assert(origPoint.x === clonePoint.x && origPoint.y === clonePoint.y,
                       `Point ${i} should be identical in original and clone`);
    }
    
    // Modify original and verify clone is independent
    originalSpline.insertPoint(new Point(0.75, 0.75));
    console.assert(originalSpline.pointCount === 4, "Original should have 4 points after modification");
    console.assert(clonedSpline.pointCount === 3, "Clone should still have 3 points after original modification");
    
    // ============================================================================
    // COMPLEX USAGE TESTS
    // ============================================================================
    
    // Create a complex spline with many points
    let complexPoints = [];
    for (let i = 0; i < 10; i++) {
        complexPoints.push({
            x: i / 10, // 0.0, 0.1, 0.2, ..., 0.9
            y: Math.sin(i * 0.5) * 0.5 + 0.5 // Values between 0-1
        });
    }
    
    let complexSpline = Spline.createFromPoints(complexPoints);
    console.assert(complexSpline.pointCount === 10, "Complex spline should have 10 points");
    
    
    // ============================================================================
    // ERROR HANDLING TESTS
    // ============================================================================
    
    // Test empty points array
    let emptyPointsError = false;
    try {
        let emptySpline = Spline.createFromPoints([]);
    } catch (error) {
        emptyPointsError = true;
    }
    console.assert(emptyPointsError, "Should throw error for empty points");
    
    // Test invalid point coordinates (outside 0-1 range)
    let invalidCoordError = false;
    try {
        let invalidCoordSpline = Spline.createFromPoints([
            {x: 0.0, y: 0.0},
            {x: 1.5, y: 0.5} // x > 1
        ]);
    } catch (error) {
        invalidCoordError = true;
    }
    console.assert(invalidCoordError, "Should throw error for invalid coordinates");
    
    // ============================================================================
    // SET-LIKE BEHAVIOR TESTS
    // ============================================================================
    
    let setSpline = Spline.create();
    
    // Add points with different x coordinates
    setSpline.insertPoint(new Point(0.1, 0.2));
    setSpline.insertPoint(new Point(0.3, 0.4));
    setSpline.insertPoint(new Point(0.5, 0.6));
    console.assert(setSpline.pointCount === 3, "Should have 3 points after initial insertion");
    
    // Try to insert a point with existing x coordinate
    let duplicateError = false;
    try {
        setSpline.insertPoint(new Point(0.3, 0.8)); // Same x as existing point
    } catch (error) {
        duplicateError = true;
    }
    console.assert(duplicateError, "Should throw error for duplicate x coordinate");
    
    // Use replaceOrInsertPoint to replace existing point
    setSpline.replaceOrInsertPoint(new Point(0.3, 0.8)); // Same x, different y
    console.assert(setSpline.pointCount === 3, "Point count should remain 3 after replaceOrInsertPoint");
    
    // Verify the replacement
    const replacedPoint2 = setSpline.getPoint(1); // Should be the point at index 1
    console.assert(replacedPoint2.x === 0.3 && replacedPoint2.y === 0.8, "Point should be replaced with new y value");
    
    console.log("Spline Test Ok");
}

module.exports.testSpline = testSpline;
