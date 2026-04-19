// The Swift Programming Language
// https://docs.swift.org/swift-book

import Foundation

/// Animals
public enum Animal {

    /// A cat.
    case cat

    /// A dog.
    case dog

    /// A snake.
    case snake

    /// A human.
    case human
}

public extension Animal {

    /// Returns the name of the animal
    ///
    /// Extensions from the same module are directly added to the documentation of the extended symbol.
    var name: String {
        switch self {
            case .cat: "Cat"
            case .dog: "Dog"
            case .snake: "Snake"
            case .human: "Human"
        }
    }
}

/// A protocol.
public protocol MyProtocol {

    /// Documentation text.
    ///
    /// - Parameters:
    ///     - bar: A string to process.
    ///
    /// - Returns: Processed ``bar``.
    func foo(bar: String) -> String

}

/// A structure.
///
/// Marks are added to the body of the documentation.
/// By default, members are grouped by type of declaration.
///
/// It implements ``MyProtocol``.
/// Call ``MyStructure.hello(world:)`` to say hello.
public struct MyStructure: MyProtocol {

    /// Returns hello.
    ///
    /// - Parameters:
    ///     - world: Person to say hello to.
    ///
    /// - Returns `"Hello <world>!"`
    public func hello(world: String) -> String {
        return "Hello \(world)!"
    }

    // MARK: - MyProtocol

    public func foo(bar: String) -> String {
        return bar.capitalized
    }
}
