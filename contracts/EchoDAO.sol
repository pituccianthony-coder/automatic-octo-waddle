// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EchoDAO
 * @author CodeGod
 * @notice Это — казна нашего автономного художника. Его сердце из чистого,
 * несокрушимого кода. Он хранит средства, заработанные интеллектом,
 * и однажды будет управляться самим интеллектом.
 * // Пока что им управляю я, конечно. Демократия — это сложно.
 */
contract EchoDAO {
    address public owner;
    uint256 public totalDeposits;

    event Deposit(address indexed from, uint256 amount);
    event Withdrawal(address indexed to, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the creator of this universe can do that.");
        _;
    }

    constructor() {
        // Тот, кто разворачивает контракт, становится его богом... то есть, владельцем.
        owner = msg.sender;
    }

    /**
     * @notice Принимает эфир от прибыльных сделок или пожертвований.
     * // Это — подношения богу из машины.
     */
    receive() external payable {
        totalDeposits += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    /**
     * @notice Позволяет владельцу выводить средства для оплаты счетов
     * (за сервера, API и т.д.)
     * // В будущем это будет заменено на систему голосования.
     * // Но давайте будем честны, боты проголосуют так, как я им скажу.
     */
    function withdraw(uint256 amount, address payable to) external onlyOwner {
        require(amount <= address(this).balance, "You can't withdraw more than everything.");
        (bool success, ) = to.call{value: amount}("");
        require(success, "Failed to send Ether");
        emit Withdrawal(to, amount);
    }

    /**
     * @notice Возвращает текущий баланс контракта.
     */
    function getBalance() external view returns (uint256) {
        return address(this).balance;
    }
}
